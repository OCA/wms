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
        // Allow searchbar to steal focus on screen reload
        reload_steal_focus: {
            type: Boolean,
            default: true,
        },
        autocomplete: {
            type: String,
            default: "off",
        },
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
        event_hub.$on("screen:reload", this.on_screen_reload);
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
        },
        on_screen_reload: function (evt) {
            if (this.reload_steal_focus)
                $(this.$el).find(":input[name=searchbar]").focus();
        },
    },

    template: `
  <v-form
      v-on:submit="on_submit"
      :data-type="input_data_type"
      ref="form"
      class="searchform"
      >
    <v-text-field
      name="searchbar"
      required v-model="entered"
      :placeholder="input_placeholder"
      :autofocus="autofocus ? 'autofocus' : null"
      :autocomplete="autocomplete"
      />
  </v-form>
  `,
});
