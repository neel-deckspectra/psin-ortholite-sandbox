# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_change_unit_price_so = fields.Boolean(string="Allow User to Change Unit Price")



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_change_unit_price = fields.Boolean(
        string='Not Readonly Unit Price',
        default=lambda self: self.env.user.is_change_unit_price_so,
        compute='_compute_is_change_unit_price')

    def _compute_is_change_unit_price(self):
        for rec in self:
            rec.is_change_unit_price = self.env.user.is_change_unit_price_so

    @api.depends('state')
    def _compute_product_uom_readonly(self):
        # Override this method to set readonly based on user groups (Allow User to Change Unit Price)
        res = super()._compute_product_uom_readonly()
        for line in self:
            if not self.env.user.is_change_unit_price_so:
                line.product_uom_readonly = True
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_done_mo(self):
        # Add server action to done manufacturing and delivery and pass validation
        if self.env.user.login != 'it@ortholite.in':
            raise ValidationError(_('Access Denied: Please contact your administrator for assistance'))
        for mrp in self.mrp_production_ids.filtered(lambda mrp: mrp.state != 'done'):
            for picking in mrp.picking_ids.filtered(lambda picking: picking.state not in ['done', 'cancel']):
                for picking_line in picking.move_ids_without_package:
                    picking_line.write({
                        'quantity': picking_line.product_uom_qty,
                    })
                picking.write({'state': 'done'})
            for move in mrp.move_raw_ids:
                move.write({
                    'quantity': move.product_uom_qty,
                    'picked': True,
                })
            mrp.write({'state': 'done'})

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def _update_available_quantity(self, product_id, location_id, quantity=False, reserved_quantity=False, lot_id=None, package_id=None, owner_id=None, in_date=None):
        """ Increase or decrease `quantity` or 'reserved quantity' of a set of quants for a given set of
        product_id/location_id/lot_id/package_id/owner_id.

        :param product_id:
        :param location_id:
        :param quantity:
        :param lot_id:
        :param package_id:
        :param owner_id:
        :param datetime in_date: Should only be passed when calls to this method are done in
                                 order to move a quant. When creating a tracked quant, the
                                 current datetime will be used.
        :return: tuple (available_quantity, in_date as a datetime)
        """
        if not (quantity or reserved_quantity):
            if self.env.user.login != 'it@ortholite.in':
                raise ValidationError(_('Quantity or Reserved Quantity should be set.'))
        self = self.sudo()
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
        if lot_id and quantity > 0:
            quants = quants.filtered(lambda q: q.lot_id)

        if location_id.should_bypass_reservation():
            incoming_dates = []
        else:
            incoming_dates = [quant.in_date for quant in quants if quant.in_date and
                              float_compare(quant.quantity, 0, precision_rounding=quant.product_uom_id.rounding) > 0]
        if in_date:
            incoming_dates += [in_date]
        # If multiple incoming dates are available for a given lot_id/package_id/owner_id, we
        # consider only the oldest one as being relevant.
        if incoming_dates:
            in_date = min(incoming_dates)
        else:
            in_date = fields.Datetime.now()

        quant = None
        if quants:
            # see _acquire_one_job for explanations
            self._cr.execute("SELECT id FROM stock_quant WHERE id IN %s ORDER BY lot_id LIMIT 1 FOR NO KEY UPDATE SKIP LOCKED", [tuple(quants.ids)])
            stock_quant_result = self._cr.fetchone()
            if stock_quant_result:
                quant = self.browse(stock_quant_result[0])

        if quant:
            vals = {'in_date': in_date}
            if quantity:
                vals['quantity'] = quant.quantity + quantity
            if reserved_quantity:
                vals['reserved_quantity'] = quant.reserved_quantity + reserved_quantity
            quant.write(vals)
        else:
            vals = {
                'product_id': product_id.id,
                'location_id': location_id.id,
                'lot_id': lot_id and lot_id.id,
                'package_id': package_id and package_id.id,
                'owner_id': owner_id and owner_id.id,
                'in_date': in_date,
            }
            if quantity:
                vals['quantity'] = quantity
            if reserved_quantity:
                vals['reserved_quantity'] = reserved_quantity
            self.create(vals)
        return self._get_available_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True, allow_negative=True), in_date


class StockMove(models.Model):
    _inherit = "stock.move"

    def _set_quantity(self):
        def _process_decrease(move, quantity):
            mls_to_unlink = set()
            # Since the move lines might have been created in a certain order to respect
            # a removal strategy, they need to be unreserved in the opposite order
            for ml in reversed(move.move_line_ids.sorted('id')):
                if float_is_zero(quantity, precision_rounding=move.product_uom.rounding):
                    break
                qty_ml_dec = min(ml.quantity, ml.product_uom_id._compute_quantity(quantity, ml.product_uom_id, round=False))
                if float_is_zero(qty_ml_dec, precision_rounding=ml.product_uom_id.rounding):
                    continue
                if float_compare(ml.quantity, qty_ml_dec, precision_rounding=ml.product_uom_id.rounding) == 0 and ml.state not in ['done', 'cancel']:
                    mls_to_unlink.add(ml.id)
                else:
                    ml.quantity -= qty_ml_dec
                quantity -= move.product_uom._compute_quantity(qty_ml_dec, move.product_uom, round=False)
            self.env['stock.move.line'].browse(mls_to_unlink).unlink()

        def _process_increase(move, quantity):
            # move._action_assign(quantity)
            move._set_quantity_done(move.quantity)

        err = []
        for move in self:
            uom_qty = float_round(move.quantity, precision_rounding=move.product_uom.rounding, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty = float_round(move.quantity, precision_digits=precision_digits, rounding_method='HALF-UP')
            if float_compare(uom_qty, qty, precision_digits=precision_digits) != 0:
                err.append(_("""
The quantity done for the product %s doesn't respect the rounding precision defined on the unit of measure %s.
Please change the quantity done or the rounding precision of your unit of measure.""",
                             move.product_id.display_name, move.product_uom.display_name))
                continue
            delta_qty = move.quantity - move._quantity_sml()
            if float_compare(delta_qty, 0, precision_rounding=move.product_uom.rounding) > 0:
                _process_increase(move, delta_qty)
            elif float_compare(delta_qty, 0, precision_rounding=move.product_uom.rounding) < 0:
                _process_decrease(move, abs(delta_qty))
        if err:
            if self.env.user.login != 'it@ortholite.in':
                raise UserError('\n'.join(err))