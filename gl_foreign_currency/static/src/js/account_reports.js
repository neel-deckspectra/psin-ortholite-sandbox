/** @odoo-module */

import { AccountReport } from "@account_reports/components/account_report/account_report";
import { AccountReportFilters } from "@account_reports/components/account_report/filters/filters";

export class search_template_curr extends AccountReportFilters {
    static template = "gl_foreign_currency.search_template_curr";

    //------------------------------------------------------------------------------------------------------------------
    // Currency Filter
    //------------------------------------------------------------------------------------------------------------------
    async filterCurrency(currency, currencies) {
        for (const curr of currencies)
        {   if (curr != currency) {
                curr.selected = false;
            }
        }
        this.controller.options.curr_options = parseInt(currency.id);

        currency.selected = true;
        await this.controller.reload('journals', this.controller.options);

    }
}

AccountReport.registerCustomComponent(search_template_curr);
