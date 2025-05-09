odoo.define('pos_table_restrictions.pos_table_editable', function(require) {
'use strict';

       const FloorScreen = require('pos_restaurant.FloorScreen');
       const { useListener } = require('web.custom_hooks');
       const Registries = require('point_of_sale.Registries');
       var session = require('web.session');

     const PosScreenRule = (FloorScreen) =>
            class extends FloorScreen {
                constructor() {
                super(...arguments);
                useListener('rename-table', this._renameTable);
                useListener('delete-table', this._deleteTable);
            }

              async _renameTable() {
                const selectedTable = this.selectedTable;
                 if (!selectedTable) return;

                 if (selectedTable.order_count != 0 && this.env.pos.config.table_order_configuration === true){
                    await this.showPopup('ErrorPopup', {
                        title: this.env._t('Alert!'),
                        body: this.env._t('Mr/Mrs/Ms ' +  session.name +' you cannot edit this Table , since the  order is not close, please close your order,   and Try Again  ..! '),
                    });
                    }

                   if (selectedTable.order_count != 0 && this.env.pos.config.table_order_configuration === true)return;
                    const { confirmed, payload: newName } = await this.showPopup('TextInputPopup', {
                    startingValue: selectedTable.name,
                    title: this.env._t('Vehicle Name ?'),
                });


                if (!confirmed) return;
                if (newName !== selectedTable.name) {
                    selectedTable.name = newName;
                    await this._save(selectedTable);
                }
            }

          async _deleteTable() {
            if (!this.selectedTable) return;
            if (!this.selectedTable.order_count != 1  && this.env.pos.config.table_order_configuration === true){
                    await this.showPopup('ErrorPopup', {
                        title: this.env._t('Alert!'),
                        body: this.env._t('Mr/Mrs/Ms ' +  session.name +' you cannot delete this Table , since the  order is not close, please close your order, and Try Again ..! '),
                    });
                 }
                if (!this.selectedTable.order_count != 1  && this.env.pos.config.table_order_configuration === true) return ;
                const { confirmed } = await this.showPopup('ConfirmPopup', {
                    title: this.env._t('Are you sure ?'),
                    body: this.env._t('Removing a table cannot be undone'),
                });

            if (!confirmed) return;
            try {
                const originalSelectedTableId = this.state.selectedTableId;
                await this.rpc({
                    model: 'restaurant.table',
                    method: 'create_from_ui',
                    args: [{ active: false, id: originalSelectedTableId }],
                });
                this.activeFloor.tables = this.activeTables.filter(
                    (table) => table.id !== originalSelectedTableId
                );
                if (this.state.selectedTableId === originalSelectedTableId) {
                    this.state.selectedTableId = null;
                }
            } catch (error) {
                if (error.message.code < 0) {
                    await this.showPopup('OfflineErrorPopup', {
                        title: this.env._t('Offline'),
                        body: this.env._t('Unable to delete table'),
                    });
                } else {
                    throw error;
                }
            }
        }
     }


   Registries.Component.extend(FloorScreen, PosScreenRule);
   return PosScreenRule;
});
