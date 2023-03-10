odoo.define("stock_release_channel.progressbar_fractional_widget", function (require) {
    "use strict";

    var utils = require("web.utils");
    var basic_fields = require("web.basic_fields");
    var FieldProgressBar = basic_fields.FieldProgressBar;

    /**
     * New node option:
     *
     * - show_fractional: Show always the numerical progress as <number> / <number>.
     */
    FieldProgressBar.include({
        /**
         * Extended so that we can choose when to show the values always
         * as a fractional part.
         */
        init: function () {
            this._super.apply(this, arguments);
            this.show_fractional = this.nodeOptions.show_fractional || false;
        },

        /**
         * @override
         * Overridden so that we show conditionally the result as a fraction.
         * Before, it was shown as a fraction only if the denominator was
         * not 100. Also: if denominator is zero, it's zero, and not 100 as
         * in the core.
         */
        _render_value: function (v) {
            var value = this.value;
            var max_value = this.max_value;
            if (!isNaN(v)) {
                if (this.edit_max_value) {
                    max_value = v;
                } else {
                    value = v;
                }
            }
            value = value || 0;
            max_value = max_value || 0;

            // Variable initialised on declaration to silent the pre-commit.
            // So the `else` part was removed.
            var widthComplete = 100;
            if (value <= max_value) {
                widthComplete = (value / max_value) * 100;
            }

            this.$(".o_progress")
                .toggleClass("o_progress_overflow", value > max_value)
                .attr("aria-valuemin", "0")
                .attr("aria-valuemax", max_value)
                .attr("aria-valuenow", value);
            this.$(".o_progressbar_complete").css("width", widthComplete + "%");

            if (!this.write_mode) {
                // This `if` is a change made on this method w.r.t. the original one.
                if (max_value !== 100 || this.show_fractional) {
                    // This variable is a change made w.r.t. the original one,
                    // because the original one set the value to 100 if the
                    // maximum value was zero.
                    var original_max_value =
                        this.recordData[this.nodeOptions.max_value];
                    this.$(".o_progressbar_value").text(
                        utils.human_number(value) +
                            " / " +
                            utils.human_number(original_max_value)
                    );
                } else {
                    this.$(".o_progressbar_value").text(
                        utils.human_number(value) + "%"
                    );
                }
            } else if (isNaN(v)) {
                this.$(".o_progressbar_value").val(
                    this.edit_max_value ? max_value : value
                );
                this.$(".o_progressbar_value").focus().select();
            }
        },
    });
});
