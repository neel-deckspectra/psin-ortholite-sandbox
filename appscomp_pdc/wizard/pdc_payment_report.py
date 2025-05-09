from odoo import api, fields, models, _
from datetime import datetime, timedelta, date


class PdcReportWizard(models.TransientModel):
    _name = 'pdc.report.wizard'
    _description = "Pdc Payment Report Details"

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    user_id = fields.Many2many('res.partner', string='Customer')
    states = fields.Selection(
        [('draft', 'Draft'), ('registered', 'Registered'), ('bounced', 'Bounced'), ('returned', 'Returned'),
         ('deposited', 'Deposited'), ('done', 'Cleared'), ('cancelled', 'Cancelled')],
        string="Status")
    current_user = fields.Many2one('res.users', 'Current User', default=lambda self: self.env.user)

    def print_pdc_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'user': self.user_id.ids,
                'state': self.states,
                'current_user': self.current_user.name,
            },
        }
        return self.env.ref('appscomp_pdc.action_pdc_payment_wizard_report').report_action(self,
                                                                                                             data=data)


class PdcReportWizardAction(models.AbstractModel):
    _name = 'report.appscomp_pdc.template_pdc_payment_qweb'
    _description = "Project Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        user = data['form']['user']
        state = data['form']['state']
        user_name = data['form']['current_user']
        date_start = datetime.strptime(start_date, '%Y-%m-%d').date()
        date_end = datetime.strptime(end_date, '%Y-%m-%d').date()
        docs = []

        if user and start_date and end_date and state:
            payment_ids = self.env['post.dated.cheques'].search(
                [('payment_date', '>=', date_start),
                 ('payment_date', '<=', date_end),
                 ('partner_id', 'in', user),
                 ('state', '=', state), ])
        if state and start_date and end_date:
            payment_ids = self.env['post.dated.cheques'].search(
                [('payment_date', '>=', date_start),
                 ('payment_date', '<=', date_end),
                 ('state', '=', state), ])
        if start_date and end_date:
            payment_ids = self.env['post.dated.cheques'].search(
                [('payment_date', '>=', date_start),
                 ('payment_date', '<=', date_end)])
        if user and start_date and end_date:
            payment_ids = self.env['post.dated.cheques'].search(
                [('payment_date', '>=', date_start),
                 ('payment_date', '<=', date_end),
                 ('partner_id', 'in', user), ])

        for payment in payment_ids:
            vals = {
                'name': payment.name,
                'payment_date': payment.payment_date,
                'partner': payment.partner_id.name,
                'amount': payment.amount,
                'currency': payment.currency_id.name,
                'bank': payment.journal_id.name,
                'memo': payment.communication,
                'payment_status': payment.state,
                'reference': payment.bank_reference,
                'Payment_invoice': payment.payment_id.name,
                'check_number': payment.journal_id.check_next_number,
                'due_date': payment.effective_date,

            }
            docs.append(vals)

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': docs,
            'start_date': start_date,
            'end_date': end_date,
            'user_name': user_name,
        }
