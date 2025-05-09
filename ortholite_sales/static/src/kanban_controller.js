/** @odoo-module */
/**
 * This file will used to hide the selected options from the list view
 */
import { KanbanController } from '@web/views/kanban/kanban_controller';
import { patch} from "@web/core/utils/patch";
const {onWillStart} = owl;
patch(KanbanController.prototype,{
/**
 * This function will used to hide the selected options from the Kanban view
 */
    setup() {
        super.setup(...arguments);
        this.rpc = this.env.services.rpc
        onWillStart(async () => {
            var self = this
            if (self.props.resModel === "sale.order") {
                self.props.archInfo.activeActions.create=false
            }
        });
    }
});
