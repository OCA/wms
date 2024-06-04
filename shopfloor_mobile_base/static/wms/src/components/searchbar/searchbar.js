/* eslint-disable strict */
/**
 * Copyright 2020 Akretion (http://www.akretion.com)
 * @author Raphaël Reverdy <raphael.reverdy@akretion.com>
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * Copyright 2021 BCIM (http://www.bcim.be)
 * @author Jacques-Etienne Baudoux <je@bcim.be>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */
import event_hub from "../../services/event_hub.js";

export var Searchbar = Vue.component("searchbar", {
    data: function () {
        return {
            entered: "",
            debounceWait: this.autosearch,
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
        // remove leading/trailing spaces from input before searching
        autotrim: {
            type: Boolean,
            default: true,
        },
        // on scanned input without end of line, the search will run after 50ms. Set to 0 to disable
        autosearch: {
            type: Number,
            default: 50,
        },
        // on manually typed input, the search will run after time. Set to 1500 (ms) as time for typing. By default, disabled, enter must be pressed
        autosearch_typing: {
            type: Number,
            default: 0,
        },
    },
    mounted: function () {
        // Force focus because when the widget is injected in the DOM
        // `inputmode` is set to `none`.
        this.capture_focus();
        /* When you click on other elements on the page
        the focus is normally obtainable via the `onblur` binding.
        However, when `click` triggers a screen reload after an api call
        that is not enough.
        */
        event_hub.$on("screen:reload", () => {
            if (this.autofocus) this.capture_focus();
        });
    },
    updated: function () {
        this.capture_focus();
    },
    computed: {
        // defined as computed property to put a new instance in cache each
        // time the reactive debounceWait is modified
        debouncedSearch() {
            return _.debounce(function (e) {
                if (
                    this.entered.length == 1 &&
                    this.debounceWait != this.autosearch_typing
                ) {
                    this.debounceWait = this.autosearch_typing;
                    if (!this.debounceWait) return;
                    return this.debouncedSearch();
                }
                if (!this.debounceWait) return;
                return this.search();
            }, this.debounceWait);
        },
    },
    watch: {
        entered: function (val) {
            if (this.autotrim) {
                let trimmed = val.trim();
                if (trimmed !== val) {
                    this.entered = trimmed;
                    return;
                }
            }
            if (!this.autosearch) return;
            if (val.length == 0) {
                this.debouncedSearch.cancel();
                this.debounceWait = this.autosearch;
                return;
            }
            return this.debouncedSearch();
        },
    },
    methods: {
        capture_focus: function () {
            if (this.autofocus && this.$refs.searchbar) {
                // We need to use both "focus" and "click" in combination
                // to make sure that the searchbar is fully focused and ready for scanning
                // without having to manually tap on it.
                // Using simply one or the other is not enough
                // to always be able to input any scanned text.
                this.$refs.searchbar.focus();
                this.$refs.searchbar.click();
            }
        },
        show_virtual_keyboard: function (elem) {
            elem.inputMode = this.input_inputmode;
            elem.classList.add("searchbar-keyboard");
        },
        hide_virtual_keyboard: function (elem) {
            elem.inputMode = "none";
            elem.classList.remove("searchbar-keyboard");
        },
        search: function () {
            // Talk to parent
            if (!this.entered) return;
            this.$emit("found", {
                text: this.entered,
                type: this.input_data_type,
            });
            if (this.debounceWait === this.autosearch && this.reset_on_submit)
                this.reset();
        },
        on_submit: function (e) {
            e.preventDefault();
            this.debouncedSearch.cancel();
            this.search();
            if (this.reset_on_submit) this.reset();
        },
        reset: function () {
            this.entered = "";
            this.hide_virtual_keyboard(this.$refs.searchbar);
        },
        onclick: function (e) {
            if (e.target.inputMode == "none") {
                this.show_virtual_keyboard(e.target);
            } else {
                this.hide_virtual_keyboard(e.target);
            }
        },
        onfocus: function (e) {
            e.target.classList.add("searchbar-scan");
        },
        onblur: function (e) {
            if (this.forcefocus) return e.target.click();
            e.target.classList.remove("searchbar-scan");
        },
    },

    template: `
  <v-form
      v-on:submit="on_submit"
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
