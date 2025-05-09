# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.tools.misc import format_date
from collections import defaultdict


class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    def _build_column_dict(
            self, col_value, col_data,
            options=None, currency=False, digits=1,
            column_expression=None, has_sublines=False,
            report_line_id=None,
    ):
        if not currency and options and options.get('curr_options'):
            cur = self.env['res.currency'].browse(options.get('curr_options'))
            currency = cur
        res = super(AccountReport, self)._build_column_dict(col_value, col_data, options, currency, digits,
                                                            column_expression, has_sublines, report_line_id)
        return res


class ReportGeneralLedger(models.AbstractModel):
    _inherit = 'account.general.ledger.report.handler'

    filter_currencys = True

    def _get_custom_display_config(self):
        res = super(ReportGeneralLedger, self)._get_custom_display_config()
        res['templates'].update({'AccountReportFilters': 'gl_foreign_currency.search_template_curr'})
        res['components'] = {'AccountReportFilters': 'gl_foreign_currency.search_template_curr'}
        return res

    def _custom_options_initializer(self, report, options, previous_options=None):
        res = super(ReportGeneralLedger, self)._custom_options_initializer(report, options, previous_options)
        if 'curr_options' in previous_options:
            options['curr_options'] = previous_options.get('curr_options')
        if self.filter_currencys:
            currencies = self.env['res.currency'].search([])
            options['currenciess'] = [{'id': c.id, 'name': c.name, 'selected': False} for c in currencies]
            if 'curr_options' in options:
                for c in options['currenciess']:
                    if c['id'] == options['curr_options']:
                        c['selected'] = True
            else:
                for c in options['currenciess']:
                    if c['id'] == self.env.user.company_id.currency_id.id:
                        c['selected'] = True
            options['currencys'] = True
            return options
        return res

    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals, warnings=None):
        if 'curr_options' in options:
            lines = []
            cur = self.env['res.currency'].browse(options.get('curr_options'))
            company_currency = self.env.company.currency_id
            date_from = fields.Date.from_string(options['date']['date_from'])
            today_date = fields.Date.today()
            company = self.env.company

            totals_by_column_group = defaultdict(lambda: {'debit': 0, 'credit': 0, 'balance': 0})
            for account, column_group_results in self._query_values(report, options):
                eval_dict = {}
                has_lines = False
                for column_group_key, results in column_group_results.items():
                    account_sum = results.get('sum', {})
                    account_un_earn = results.get('unaffected_earnings', {})

                    account_debit = account_sum.get('debit', 0.0) + account_un_earn.get('debit', 0.0)
                    account_credit = account_sum.get('credit', 0.0) + account_un_earn.get('credit', 0.0)
                    account_balance = account_sum.get('balance', 0.0) + account_un_earn.get('balance', 0.0)

                    debit = company_currency._convert(account_debit, cur, company, today_date)
                    credit = company_currency._convert(account_credit, cur, company, today_date)
                    balance = company_currency._convert(account_balance, cur, company, today_date)

                    eval_dict[column_group_key] = {
                        'amount_currency': account_sum.get('amount_currency', 0.0) + account_un_earn.get(
                            'amount_currency', 0.0),
                        'debit': debit,
                        'credit': credit,
                        'balance': balance,
                    }

                    max_date = account_sum.get('max_date')
                    has_lines = has_lines or (max_date and max_date >= date_from)

                    totals_by_column_group[column_group_key]['debit'] += debit
                    totals_by_column_group[column_group_key]['credit'] += credit
                    totals_by_column_group[column_group_key]['balance'] += balance

                lines.append(self._get_account_title_line(report, options, account, has_lines, eval_dict))

            # Report total line.
            for totals in totals_by_column_group.values():
                totals['balance'] = company_currency.round(totals['balance'])

            # Tax Declaration lines.
            journal_options = report._get_options_journals(options)
            if len(options['column_groups']) == 1 and len(journal_options) == 1 and journal_options[0]['type'] in (
                    'sale', 'purchase'):

                new_tax_lines = self._tax_declaration_lines(report, options, journal_options[0]['type'])
                for line in new_tax_lines:
                    for col in line.get('columns'):
                        if col.get('no_format'):
                            converted_amt = company_currency._convert(col.get('no_format'), cur, company, today_date)
                            col['no_format'] = converted_amt
                            col['name'] = report.format_value(options, converted_amt, currency=cur,
                                                              figure_type='monetary')

                lines += new_tax_lines

            # Total line
            lines.append(self._get_total_line(report, options, totals_by_column_group))

            return [(0, line) for line in lines]
        return super(ReportGeneralLedger, self)._dynamic_lines_generator(report, options,
                                                                         all_column_groups_expression_totals, warnings)

    def _get_account_title_line(self, report, options, account, has_lines, eval_dict):
        ress = super(ReportGeneralLedger, self)._get_account_title_line(report, options, account, has_lines, eval_dict)
        if 'curr_options' in options:
            cur = self.env['res.currency'].browse(options.get('curr_options'))

            line_columns = []
            for column in options['columns']:
                col_value = eval_dict[column['column_group_key']].get(column['expression_label'])
                col_expr_label = column['expression_label']

                if col_value is None or (col_expr_label == 'amount_currency' and not account.currency_id):
                    line_columns.append({})

                else:
                    if col_expr_label == 'amount_currency':
                        formatted_value = report.format_value(options, col_value, currency=account.currency_id,
                                                              figure_type=column['figure_type'])
                    else:
                        if options.get('curr_options'):
                            formatted_value = report.format_value(options, col_value, currency=cur,
                                                                  figure_type=column['figure_type']
                                                                  , blank_if_zero=col_expr_label != 'balance')
                        else:
                            formatted_value = report.format_value(options, col_value, figure_type=column['figure_type'])

                    line_columns.append({
                        'name': formatted_value,
                        'no_format': col_value,
                        'class': 'number',
                    })

            line_id = report._get_generic_line_id('account.account', account.id)
            return {
                'id': line_id,
                'name': f'{account.code} {account.name}',
                'columns': line_columns,
                'level': 1,
                'unfoldable': has_lines,
                'unfolded': has_lines and (line_id in options.get('unfolded_lines') or options.get('unfold_all')),
                'expand_function': '_report_expand_unfoldable_line_general_ledger',
            }
        return ress

    def _get_total_line(self, report, options, eval_dict):
        res = super(ReportGeneralLedger, self)._get_total_line(report, options, eval_dict)
        if 'curr_options' in options:
            line_columns = []
            for column in options['columns']:
                col_value = eval_dict[column['column_group_key']].get(column['expression_label'])
                if col_value is None:
                    line_columns.append({})
                else:
                    if options.get('curr_options'):
                        formatted_value = report.format_value(options, col_value,
                                                              currency=self.env['res.currency'].browse(
                                                                  options.get('curr_options')), figure_type='monetary')

                    else:
                        formatted_value = report.format_value(options, col_value, blank_if_zero=False,
                                                              figure_type='monetary')

                    line_columns.append({
                        'name': formatted_value,
                        'no_format': col_value,
                        'class': 'number',
                    })

            return {
                'id': report._get_generic_line_id(None, None, markup='total'),
                'name': _('Total'),
                'level': 1,
                'columns': line_columns,
            }
        return res

    def _get_aml_values(self, report, options, expanded_account_ids, offset=0, limit=None):
        original, has_more_original = super(ReportGeneralLedger, self)._get_aml_values(report, options,
                                                                                       expanded_account_ids, offset,
                                                                                       limit)
        company_currency = self.env.company.currency_id
        currency_id = self.env['res.currency'].browse(options.get('curr_options', False))
        today_date = fields.Date.today()
        company = self.env.company

        if currency_id and currency_id != company_currency:
            rslt = {account_id: {} for account_id in expanded_account_ids}
            aml_query, aml_params = self._get_query_amls(report, options, expanded_account_ids, offset=offset,
                                                         limit=limit)
            self._cr.execute(aml_query, aml_params)
            aml_results_number = 0
            has_more = False
            for aml_result in self._cr.dictfetchall():
                aml_results_number += 1
                if aml_results_number == limit:
                    has_more = True
                    break

                if aml_result['ref']:
                    aml_result['communication'] = f"{aml_result['ref']} - {aml_result['name']}"
                else:
                    aml_result['communication'] = aml_result['name']

                # The same aml can return multiple results when using account_report_cash_basis module, if the receivable/payable
                # is reconciled with multiple payments. In this case, the date shown for the move lines actually corresponds to the
                # reconciliation date. In order to keep distinct lines in this case, we include date in the grouping key.
                aml_key = (aml_result['id'], aml_result['date'])

                aml_result['debit'] = company_currency._convert(aml_result['debit'], currency_id, company, today_date)
                aml_result['credit'] = company_currency._convert(aml_result['credit'], currency_id, company, today_date)
                aml_result['balance'] = company_currency._convert(aml_result['balance'], currency_id, company,
                                                                  today_date)

                account_result = rslt[aml_result['account_id']]
                if not aml_key in account_result:
                    account_result[aml_key] = {col_group_key: {} for col_group_key in options['column_groups']}

                already_present_result = account_result[aml_key][aml_result['column_group_key']]
                if already_present_result:
                    # In case the same move line gives multiple results at the same date, add them.
                    # This does not happen in standard GL report, but could because of custom shadowing of account.move.line,
                    # such as the one done in account_report_cash_basis (if the payable/receivable line is reconciled twice at the same date).
                    already_present_result['debit'] += aml_result['debit']
                    already_present_result['credit'] += aml_result['credit']
                    already_present_result['balance'] += aml_result['balance']
                    already_present_result['amount_currency'] += aml_result['amount_currency']
                else:
                    account_result[aml_key][aml_result['column_group_key']] = aml_result

            return rslt, has_more
        return original, has_more_original

    def _get_aml_line(self, report, parent_line_id, options, eval_dict, init_bal_by_col_group):
        ress = super(ReportGeneralLedger, self)._get_aml_line(report, parent_line_id, options, eval_dict,
                                                              init_bal_by_col_group)
        if 'curr_options' in options:
            cur = self.env['res.currency'].browse(options.get('curr_options'))
            line_columns = []
            for column in options['columns']:
                col_expr_label = column['expression_label']
                col_value = eval_dict[column['column_group_key']].get(col_expr_label)

                if col_value is None:
                    line_columns.append({})
                else:
                    col_class = 'number'

                    if col_expr_label == 'amount_currency':
                        currency = self.env['res.currency'].browse(eval_dict[column['column_group_key']]['currency_id'])

                        formatted_value = report.format_value(options,
                                                              col_value, currency=currency,
                                                              figure_type=column['figure_type'])

                    elif col_expr_label == 'date':
                        formatted_value = format_date(self.env, col_value)
                        col_class = 'date'

                    elif col_expr_label == 'balance':
                        col_value += init_bal_by_col_group[column['column_group_key']]
                        formatted_value = report.format_value(options,
                                                              col_value, currency=cur,
                                                              figure_type=column['figure_type'], blank_if_zero=False)

                    elif col_expr_label == 'communication' or col_expr_label == 'partner_name':
                        col_class = 'o_account_report_line_ellipsis'
                        formatted_value = report.format_value(options, col_value, figure_type=column['figure_type'])

                    else:
                        formatted_value = report.format_value(options,
                                                              col_value, currency=cur,
                                                              figure_type=column['figure_type'], blank_if_zero=False)
                        if col_expr_label not in ('debit', 'credit'):
                            col_class = ''

                    line_columns.append({
                        'name': formatted_value,
                        'no_format': col_value,
                        'class': col_class,
                    })

            aml_id = None
            move_name = None
            caret_type = None
            for column_group_dict in eval_dict.values():
                aml_id = column_group_dict.get('id', '')
                if aml_id:
                    if column_group_dict.get('payment_id'):
                        caret_type = 'account.payment'
                    else:
                        caret_type = 'account.move.line'
                    move_name = column_group_dict['move_name']
                    break

            return {
                'id': report._get_generic_line_id('account.move.line', aml_id, parent_line_id=parent_line_id),
                'caret_options': caret_type,
                'parent_id': parent_line_id,
                'name': move_name,
                'columns': line_columns,
                'level': 3,
            }
        return ress

    def _get_initial_balance_values(self, report, account_ids, options):
        res = super(ReportGeneralLedger, self)._get_initial_balance_values(report, account_ids, options)
        today_date = fields.Date.today()
        if 'curr_options' in options:
            cur = self.env['res.currency'].browse(options.get('curr_options'))
            company_currency = self.env.company.currency_id
            company = self.env.company

            queries = []
            params = []
            for column_group_key, options_group in report._split_options_per_column_group(options).items():
                new_options = self._get_options_initial_balance(options_group)
                user_company = self.env.company
                conversion_date = options['date']['date_to']
                ct_query = self.env['res.currency']._get_query_currency_table(user_company.id, conversion_date)

                tables, where_clause, where_params = report._query_get(new_options, 'normal', domain=[
                    ('account_id', 'in', account_ids),
                    ('account_id.include_initial_balance', '=', True),
                ])
                params.append(column_group_key)
                params += where_params
                queries.append(f"""
                    SELECT
                        account_move_line.account_id                                                          AS groupby,
                        'initial_balance'                                                                     AS key,
                        NULL                                                                                  AS max_date,
                        %s                                                                                    AS column_group_key,
                        COALESCE(SUM(account_move_line.amount_currency), 0.0)                                 AS amount_currency,
                        SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                        SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance
                    FROM {tables}
                    LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                    WHERE {where_clause}
                    GROUP BY account_move_line.account_id
                """)
            self._cr.execute(" UNION ALL ".join(queries), params)

            init_balance_by_col_group = {
                account_id: {column_group_key: {} for column_group_key in options['column_groups']}
                for account_id in account_ids
            }
            for result in self._cr.dictfetchall():
                init_balance_by_col_group[result['groupby']][result['column_group_key']] = result
                result['debit'] = company_currency._convert(result['debit'], cur, company, today_date)
                result['credit'] = company_currency._convert(result['credit'], cur, company, today_date)
                result['balance'] = company_currency._convert(result['balance'], cur, company, today_date)
            accounts = self.env['account.account'].browse(account_ids)
            return {
                account.id: (account, init_balance_by_col_group[account.id])
                for account in accounts
            }
        return res
