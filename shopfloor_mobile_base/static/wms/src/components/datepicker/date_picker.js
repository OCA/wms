/**
 * Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
 * License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
 */

function maskString(input, mask, maskChar = "#") {
    if (!input) return "";
    // 1. Sanitize: Remove existing separators so we only have raw data
    // This prevents "2020-3" from becoming "2020--3" on double-processing
    const cleanInput = input.replace(/[^a-zA-Z0-9]/g, "");

    const characters = cleanInput.split("");
    let result = "";

    for (const char of mask) {
        if (characters.length === 0) break;

        if (char === maskChar) {
            result += characters.shift();
        } else {
            result += char;
        }
    }

    return result;
}

export var DatePicker = Vue.component("date-picker-input", {
    data: function () {
        return {
            date: "", // Iso format (YYYY-MM-DD)
            dateInput: "", // Formatted display (DD/MM/YYYY or similar according to locale)
            showInvalidDateInputMessage: false,

            // Control menu state manually to prevent closing during month/year navigation.
            menu: false,
        };
    },
    computed: {
        userLocale: function () {
            const lang = this.$root.user?.lang || "en-US";
            return lang.replace("_", "-").toLowerCase();
        },
        dateFormatter: function () {
            return new Intl.DateTimeFormat(this.userLocale);
        },
        dateFormat: function () {
            const sample = new Date(2025, 10, 10);
            const parts = this.dateFormatter.formatToParts(sample);
            return parts
                .map((p) => {
                    if (p.type === "day") return "dd";
                    if (p.type === "month") return "MM";
                    if (p.type === "year") return "yyyy";
                    return p.value;
                })
                .join("");
        },
        dateMask: function () {
            const sample = new Date(2025, 10, 10);
            return this.dateFormatter.format(sample).replace(/[0-9]/g, "#");
        },
    },
    methods: {
        onDateChange(newDate) {
            this.menu = false;
            this.dateInput = "";
            this.showInvalidDateInputMessage = false;
            this.$emit("dateChange", newDate);
        },
        /**
         * Forces a synchronization between the Vue component state and the native DOM input.
         * * This bypasses Vue's reactivity optimization which may skip a DOM update if the
         * internal data value remains unchanged after an invalid user input (e.g., typing
         * past a character limit). By briefly clearing and then restoring the value
         * during the next DOM update cycle, we ensure the rendered <input> element
         * accurately reflects the component's state.
         *
         * @private
         * @returns {void}
         */
        _force_dateInput_refresh() {
            const backup = this.dateInput;
            this.dateInput += "a";
            this.$nextTick(() => {
                this.dateInput = backup;
            });
        },
        onInput(newInput) {
            this.showInvalidDateInputMessage = false;

            if (newInput === null) {
                this.dateInput = "";
                return;
            }

            const lastChar = newInput.slice(-1);
            if (
                (!/[0-9]/.test(lastChar) && newInput.length > this.dateInput.length) ||
                newInput.length > this.dateMask.length
            ) {
                this._force_dateInput_refresh();
                return;
            }

            const maskedValue = maskString(newInput.replace(/\D/g, ""), this.dateMask);
            this.dateInput = maskedValue;
        },
        validateAndSync() {
            if (!this.dateInput) return;

            const sep = this.dateMask.match(/[^#]/)[0];

            const dateParts = this.dateInput.split(sep);
            const fmtParts = this.dateFormat.split(sep);

            if (dateParts.length !== fmtParts.length) {
                this.showInvalidDateInputMessage = true;
                return;
            }

            let year, month, day;
            for (let i = 0; i < dateParts.length; i++) {
                switch (fmtParts[i]) {
                    case "dd":
                        day = dateParts[i];
                        break;
                    case "MM":
                        month = dateParts[i];
                        break;
                    default:
                        year = dateParts[i];
                }
            }

            // ↓ suppose 2000s in case of < 4 digits year
            year = year.padStart(4, "20");
            const isoDate = `${year}-${month}-${day}`;
            if (!isNaN(Date.parse(isoDate))) {
                this.date = isoDate;
                this.menu = false;
                this.dateInput = "";
                this.$emit("dateChange", this.date);
            } else {
                this.showInvalidDateInputMessage = true;
            }
        },
    },
    template: `
    <v-menu
        v-model="menu"
        :close-on-content-click="false"
        transition="scale-transition"
        offset-y
        min-width="auto"
    >
        <template v-slot:activator="{ on, attrs }">
            <v-text-field
                :value="dateInput"
                @input="onInput"
                :error-messages="showInvalidDateInputMessage ? 'invalid input' : ''"
                :label="\`Select expiry date (\${dateFormat})\`"
                prepend-icon="mdi-calendar"
                v-bind="attrs"
                clearable
                @click:prepend="menu=true"
                @keyup.enter="validateAndSync"
                @blur="validateAndSync"
            />
        </template>
        <v-date-picker
            v-model="date"
            :locale="userLocale"
            @change="onDateChange"
        />
    </v-menu>
    `,
});
