odoo.define('WebFormImage.show_image', function (require) {
    "use strict";
    var core = require('web.core');
    var QWeb = core.qweb;
    var form_common = require('web.form_common');
    var form_widget_registry = core.form_widget_registry;

    var WebFormWidget = form_common.AbstractField.extend({
        render_value: function () {
            this._super.apply(this, arguments);
            var self = this;
            self.$el.addClass('o_form_field_image');
            self.$el.html(QWeb.render('FormView.row.image', {
                'widget': this,
                'src': this.get_value(),
            }));
        },
    });

    form_widget_registry.add('form_image', WebFormWidget);
});

