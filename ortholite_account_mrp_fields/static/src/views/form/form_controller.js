/** @odoo-module */

import { FormController } from '@web/views/form/form_controller';
import { patch } from "@web/core/utils/patch";
import { onWillStart } from '@odoo/owl';

patch(FormController.prototype, {
    /**
     * @override
     */
    setup() {
        super.setup()
        onWillStart(async () => {
            this.isAdminUser = await this.user.hasGroup('base.group_erp_manager');
        });
    },

    /**
     * @override
     * Handle the visibility of the duplicate button based on the group
     */
    getStaticActionMenuItems() {
        const menuItems = super.getStaticActionMenuItems();
        if (menuItems.duplicate) {
            // assigne value to not bypass the actual condition
            const isAvailable = menuItems.duplicate.isAvailable();
            menuItems.duplicate.isAvailable = () =>  isAvailable && this.isAdminUser;
        }
        return menuItems
    }
});
