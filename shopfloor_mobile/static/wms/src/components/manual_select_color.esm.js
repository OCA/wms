/**
 * Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

// Overriding manual-select from shopfloor_mobile_base
const Base = Vue.options.components["manual-select"];
const Custom = Base.extend({
    methods: {
        selected_color_klass(rec, modifier) {
            let color;
            if (rec && rec.qty_done && rec.quantity) {
                if (rec.qty_done < rec.quantity)
                    color = this.utils.colors.color_for("item_selected_partial");
                if (rec.qty_done > rec.quantity)
                    color = this.utils.colors.color_for("item_selected_excess");
                if (color) return "active " + color + (modifier ? " " + modifier : "");
            }
            return Base.options.methods.selected_color_klass.call(this, rec, modifier);
        },
    },
});

Vue.component("manual-select", Custom);
