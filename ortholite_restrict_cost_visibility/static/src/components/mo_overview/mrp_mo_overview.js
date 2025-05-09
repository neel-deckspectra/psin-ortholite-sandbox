/** @odoo-module **/

import { onWillStart, onWillRender } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";

import { MoOverview } from "@mrp/components/mo_overview/mrp_mo_overview"

patch(MoOverview.prototype, {
    setup() {
        super.setup();
        this.user = useService("user");
        onWillStart(async () => {
            this.hasGroupCostVisibility = await this.user.hasGroup("ortholite_restrict_cost_visibility.group_cost_visibility");
        });
        onWillRender(() => {
            if (!this.hasGroupCostVisibility) {
                this.state.showOptions.moCosts = false,
                this.state.showOptions.realCosts = false
            }
        })
    },
});
