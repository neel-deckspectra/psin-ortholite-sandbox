/** @odoo-module */
/**
 * This file will used to hide the selected options from the form view
 */
import { FormController} from "@web/views/form/form_controller";
import { patch} from "@web/core/utils/patch";
const { onWillStart} = owl;
patch(FormController.prototype,{
/**
 * This function will used to hide the selected options from the form view
 */
    setup() {
        super.setup(...arguments);
        this.rpc = this.env.services.rpc
        onWillStart(async () => {
            var self = this
            if (self.props.resModel === "sale.order") {
                self.canCreate = false
            }
        });
    }
});
