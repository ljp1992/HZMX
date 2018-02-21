odoo.define('add_button_in_tree_view.add_tree_view_button', function (require) {
    "use strict";

    var show_button_model = ['b2b.upc.list'];//哪些模型显示导入按钮
    var ListView = require('web.ListView');

    ListView.include({
        render_buttons: function () {
            var self = this;
            this._super.apply(this, arguments);
            var tree_model = this.dataset.model;
            for(var i=0; i<show_button_model.length; i++) {
                if (tree_model == show_button_model[i]){
                    var button2 = $("<button type='button' class='btn btn-sm btn-default abc'>导入excel</button>")
                        .click(this.proxy('popup_import_wizard'));
                    this.$buttons.append(button2);
                }
            }
        },
        popup_import_wizard: function () {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'import.wizard',
                views: [[false, 'form']],
                view_mode: "form",
                view_type: 'form',
                view_id: 'import_wizard_form',
                target: 'new',
            });
        },
    });

});
