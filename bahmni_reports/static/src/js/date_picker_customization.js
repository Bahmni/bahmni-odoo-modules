odoo.define('bahmni_reports.date_picker_customization', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var datepicker = require('web.datepicker');

    var CustomDateWidget = datepicker.DateWidget.include({
        start: function () {
            this._super.apply(this, arguments);
            this.$datepicker.on('mouseenter', 'td.ui-datepicker-unselectable', this._onUnselectableDayHover.bind(this));
        },
        _onUnselectableDayHover: function (event) {
            event.preventDefault();
            event.stopPropagation();
            var tooltipText = this._getUnselectableDayTooltip(event.currentTarget);
            this.$datepicker.tooltip({
                title: tooltipText,
                container: 'body',
                trigger: 'manual',
            }).tooltip('show');
        },
        _getUnselectableDayTooltip: function (dayElement) {
            var day = dayElement.textContent;
            var month = this.$datepicker.find('.ui-datepicker-month').val();
            var year = this.$datepicker.find('.ui-datepicker-year').val();
            var unselectableDate = new Date(year, month, day);
            return unselectableDate > new Date() ? 'Future Date' : 'Unavailable Date';
        },
    });

    core.action_registry.add('web_custom_datepicker', CustomDateWidget);

    return {
        CustomDateWidget: CustomDateWidget,
    };
});

