# -*- coding: utf-8 -*-

#    Custom extension for merge.rfq wizard

from odoo import models, _
from odoo.exceptions import UserError

class MergeRfqExtended(models.TransientModel):
    _inherit = 'merge.rfq'

    def action_merge_orders(self):
        res = super(MergeRfqExtended, self).action_merge_orders()
        purchase_orders = self.env["purchase.order"].browse(
            self._context.get("active_ids", []))
        if self.merge_type in ['cancel_and_new', 'delete_and_new']:
            new_po = self.env["purchase.order"].browse(
                [po.id for po in purchase_orders if po.state in ['draft', 'sent']])
            if new_po:
                new_po = new_po[0]
                origins = set(order.origin for order in purchase_orders if order.origin)
                new_po.origin = ', '.join(origins)
        else:
            selected_po = self.purchase_order_id
            if selected_po:
                origins = set(order.origin for order in purchase_orders if order.origin)
                selected_po.origin = ', '.join(origins)
        return res