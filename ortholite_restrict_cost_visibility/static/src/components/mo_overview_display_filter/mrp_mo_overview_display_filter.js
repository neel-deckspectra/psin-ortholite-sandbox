/** @odoo-module **/

import { onWillStart, onWillRender } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";

import { MoOverviewDisplayFilter } from "@mrp/components/mo_overview_display_filter/mrp_mo_overview_display_filter"

patch(MoOverviewDisplayFilter.prototype, {
    setup() {
        super.setup()
        this.user = useService("user");
        onWillStart(async () => {
            this.hasGroupCostVisibility = await this.user.hasGroup("ortholite_restrict_cost_visibility.group_cost_visibility");
        });
        onWillRender(() => {
            if (!this.hasGroupCostVisibility) {
                delete this.displayOptions.unitCosts;
                delete this.displayOptions.moCosts;
                delete this.displayOptions.realCosts;
            }
        })
    }
})
