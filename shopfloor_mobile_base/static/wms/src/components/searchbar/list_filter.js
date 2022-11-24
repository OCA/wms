/**
 * Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
 * License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
 */

export var ListFilter = Vue.component("list-filter", {
    data: function () {
        return {
            entered: "",
        };
    },
    props: {
        input_placeholder: {
            type: String,
            default: "",
        },
    },
    methods: {
        on_submit: function (event) {
            event.preventDefault();
            this.$emit("found", {
                text: this.entered,
            });
        },
        on_clear: function (event) {
            this.entered = "";
            this.on_submit(event);
        },
    },
    template: `
    <v-form
      v-on:submit="on_submit"
      ref="form"
      class="listfilterform"
    >
      <v-text-field
        name="list_filter"
        v-model="entered"
        :placeholder="input_placeholder"
        clearable
        @click:clear="on_clear"
      />
    </v-form>
  `,
});
