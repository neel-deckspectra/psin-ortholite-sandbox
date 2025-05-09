/** @odoo-module */
/**
 * This file will used to hide the selected options from the list view
 */
import { ListController} from '@web/views/list/list_controller';
import { patch} from "@web/core/utils/patch";
const {onWillStart} = owl;
patch(ListController.prototype, {
/**
 * This function will used to hide the selected options from the list view
 */
    setup() {
        super.setup(...arguments);
        this.rpc = this.env.services.rpc
        onWillStart(async () => {
            var self = this
            if (self.props.resModel === "sale.order") {
                self.activeActions.create = false;
            }
        });
    }
});
