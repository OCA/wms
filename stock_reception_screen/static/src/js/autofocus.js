odoo.define("stock_reception_screen.autofocus", function(require){
    "use strict";
    var FormRenderer = require('web.FormRenderer');

    // Implements the autofocus on each form render, the field that need
    // to have the focus on each step of the state machine is set in a
    // compute field

    FormRenderer.include({
        _custom_autofocus: function() {
            if (this.mode === 'readonly') {
                return;
            }
            if (this.state["model"] != "stock.reception.screen"){
                return;
            }
            var widgets = this.allFieldWidgets[this.state.id];
            var field2focus = this.state.fields["current_step_focus_field"].value;
            var focusWidget;
            for (var i = 0; i < (widgets ? widgets.length : 0); i++) {
                if (widgets[i].name == "current_step_focus_field") {
                    field2focus = widgets[i].value;
                    break;
                }
            }
            if (!field2focus){
                return;
            }
            // Using this.state.fields["current_step_focus_field"].value
            // is empty, does not work ?
            for (var i = 0; i < (widgets ? widgets.length : 0); i++) {
                if (widgets[i].name == field2focus) {
                    focusWidget = widgets[i];
                    break;
                }
            }
            if (focusWidget) {
                if (focusWidget.isFocusable) {
                    this.defaultFocusField = focusWidget;
                    focusWidget.activate({noselect: false, noAutomaticCreate: true});
                }
            }
        },
        _updateView: function ($newContent) {
            this._super.apply(this, arguments);
            this._custom_autofocus();
        },
        // I thought this would fix the the fact that the autofocus does not
        // work on first load but only on each button click.
        // start: function () {
        //     var self = this;
        //     var res = this._super.apply(this, arguments);
        //     return res.then(function() {
        //         self._custom_autofocus();
        //     });
        }
    });

});
