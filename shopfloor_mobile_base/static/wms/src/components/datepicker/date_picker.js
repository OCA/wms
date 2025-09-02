/**
 * Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
 * Copyright 2025 ACSONE SA/NV (https://www.acsone.com)
 * License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
 */

import event_hub from "../../services/event_hub.js";

function getFormatAndMask(locale) {
    const sample = new Date(2025, 8, 2); // 2 septembre 2025
    const parts = new Intl.DateTimeFormat(locale).formatToParts(sample);

    let format = "";
    let mask = "";

    for (const p of parts) {
        if (p.type === "day") {
            format += "dd";
            mask += "##";
        } else if (p.type === "month") {
            format += "MM";
            mask += "##";
        } else if (p.type === "year") {
            format += "yyyy";
            mask += "####";
        } else if (p.type === "literal") {
            format += p.value;
            mask += p.value;
        }
    }
    return {format, mask};
}

Vue.directive("date-mask", {
    bind(el, binding) {
        const locale = binding.value || navigator.language || "en-US";
        const {format, mask} = getFormatAndMask(locale);

        el.addEventListener("input", (e) => {
            let v = e.target.value.replace(/\D/g, ""); // Only digits
            if (v.length > 8) v = v.slice(0, 8);

            // Detects separator (first non # in the mask)
            const sep = mask.match(/[^#]/)?.[0] || "/";
            const order = format.split(sep); // Ex: ["dd","MM","yyyy"]

            const chunks = [];
            let cursor = 0;

            order.forEach((token) => {
                const size = token === "yyyy" ? 4 : 2;
                if (v.length >= cursor + size) {
                    chunks.push(v.slice(cursor, cursor + size));
                } else if (v.length > cursor) {
                    chunks.push(v.slice(cursor));
                }
                cursor += size;
            });

            e.target.value = chunks.join(sep);

            // Propagate to v-model
            e.target.dispatchEvent(new Event("input"));
        });
    },
});

export var DatePicker = Vue.component("date-picker-input", {
    props: {
        handler_to_update_date: Function,
        locale: {
            type: String,
            default: () => navigator.language || "en-US",
        },
    },
    data() {
        const {format, mask} = getFormatAndMask(this.locale);
        return {
            date: "", // Iso format (YYYY-MM-DD)
            dateInput: "", // Formatted display (DD/MM/YYYY or similar according to locale)
            menu: false,
            format,
            mask,
        };
    },
    watch: {
        date(newVal) {
            if (newVal) {
                this.dateInput = this.formatISOToInput(newVal);
            } else {
                this.dateInput = "";
            }
            this.$emit("date_picker_selected", newVal);
        },
    },
    mounted() {
        event_hub.$on("datepicker:newdate", (data) => {
            this.date = this.handler_to_update_date(data);
        });
    },
    methods: {
        parseInput() {
            if (!this.dateInput) return null;

            // Detects separator (first non # in the mask)
            const sepMatch = this.mask.match(/[^#]/);
            const sep = sepMatch ? sepMatch[0] : "/";

            const parts = this.dateInput.split(sep);
            const order = this.format.split(sep); // Ex: ["dd","MM","yyyy"]

            let day = null,
                month = null,
                year = null;
            order.forEach((token, i) => {
                if (token === "dd") day = parts[i];
                if (token === "MM") month = parts[i];
                if (token === "yyyy") year = parts[i];
            });

            if (!day || !month || !year) return null;

            const parsed = new Date(`${year}-${month}-${day}`);
            return isNaN(parsed.getTime()) ? null : parsed.toISOString().substr(0, 10);
        },

        onBlur() {
            if (!this.dateInput) {
                this.date = "";
                return;
            }
            const parts = new Intl.DateTimeFormat(this.locale)
                .formatToParts(new Date(2025, 8, 2)) // Model
                .filter((p) => ["day", "month", "year"].includes(p.type))
                .map((p) => p.type);

            const sep = this.dateInput.match(/\D/)[0];
            const values = this.dateInput.split(sep);

            let day = null,
                month = null,
                year = null;
            parts.forEach((token, i) => {
                if (token === "day") day = values[i];
                if (token === "month") month = values[i];
                if (token === "year") year = values[i];
            });

            const parsed = new Date(`${year}-${month}-${day}`);
            if (!isNaN(parsed.getTime())) {
                this.date = parsed.toISOString().substr(0, 10);
            }
        },

        formatISOToInput(iso) {
            if (!iso) return "";
            const d = new Date(iso);
            return new Intl.DateTimeFormat(this.locale).format(d);
        },
    },
    template: `
    <v-menu
      v-model="menu"
      transition="scale-transition"
      offset-y
      min-width="auto"
    >
      <template v-slot:activator="{ on, attrs }">
        <v-text-field
          v-model="dateInput"
          v-date-mask="locale"
          :label="\`Select expiry date (\${format})\`"
          prepend-icon="mdi-calendar"
          v-bind="attrs"
          v-on="on"
          clearable
          @blur="onBlur"
        />
      </template>
      <v-date-picker
        v-model="date"
        :locale="locale"
        @input="menu = false"
      />
    </v-menu>
  `,
});
