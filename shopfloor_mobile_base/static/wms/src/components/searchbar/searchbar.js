/* eslint-disable strict */
/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Raphaël Reverdy <raphael.reverdy@akretion.com>
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * Copyright 2021 BCIM (http://www.bcim.be)
 * @author Jacques-Etienne Baudoux <je@bcim.be>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

Vue.component("searchbar", {
    data: function() {
        return {
            entered: "",
        };
    },
    props: {
        autofocus: {
            type: Boolean,
            default: true,
        },
        forcefocus: {
            type: Boolean,
            default: false,
        },
        autocomplete: {
            type: String,
            default: "off",
        },
        input_type: {
            type: String,
            default: "text",
        },
        input_inputmode: {
            type: String,
            default: "text",
        },
        input_label: String,
        input_placeholder: String,
        input_data_type: String,
        reset_on_submit: {
            type: Boolean,
            default: true,
        },
    },
    mounted: function() {
        // As the inputMode is set to none when inserted in the DOM, we need to force the focus
        if (this.autofocus) this.$refs.searchbar.focus();
    },
    methods: {
        show_virtual_keyboard: function(elem) {
            elem.inputMode = this.input_inputmode;
            elem.classList.add("searchbar-keyboard");
        },
        hide_virtual_keyboard: function(elem) {
            elem.inputMode = "none";
            elem.classList.remove("searchbar-keyboard");
        },
        search: function(e) {
            e.preventDefault();
            // Talk to parent
            this.$emit("found", {
                text: this.entered,
                type: e.target.dataset.type,
            });
            if (this.reset_on_submit) this.reset();
        },
        reset: function() {
            this.entered = "";
            this.hide_virtual_keyboard(this.$refs.searchbar);
        },
        onclick: function(e) {
            if (e.target.inputMode == "none") {
                this.show_virtual_keyboard(e.target);
            } else {
                this.hide_virtual_keyboard(e.target);
            }
        },
        onfocus: function(e) {
            e.target.classList.add("searchbar-scan");
        },
        onblur: function(e) {
            if (this.forcefocus) return e.target.click();
            e.target.classList.remove("searchbar-scan");
        },
    },

    template: `
  <v-form
      v-on:submit="search"
      :data-type="input_data_type"
      class="searchform"
      >
    <div class="searchbar v-input v-text-field">
      <label class="v-label" v-if="input_label">{{ input_label }}</label>
      <input
        ref="searchbar"
        required v-model="entered"
        :type="input_type"
        :inputmode="autofocus ? 'none' : input_inputmode"
        :placeholder="input_placeholder"
        :autofocus="autofocus ? 'autofocus' : null"
        :autocomplete="autocomplete"
        @focus="onfocus"
        @blur="onblur"
        @click="onclick"
        />
      </div>
  </v-form>
  `,
});
