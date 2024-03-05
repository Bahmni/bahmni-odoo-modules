odoo.define('stock_report.required_fields_highlight', function (require) {
    "use strict";

    var core = require('web.core');
    var form_widgets = require('web.form_widgets');

    var FieldChar = form_widgets.FieldChar;

    var RequiredFieldHighlight = FieldChar.extend({
        init: function () {
            this._super.apply(this, arguments);
            // Add a class to required fields
            if (this.field.required) {
                this.$el.addClass('oe_required_field');
            }
        },
    });

    core.form_widget_registry.add('required_field_highlight', RequiredFieldHighlight);

    return {
        RequiredFieldHighlight: RequiredFieldHighlight,
    };
});

