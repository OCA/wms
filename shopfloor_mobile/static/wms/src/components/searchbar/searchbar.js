/* eslint-disable strict */
Vue.component("searchbar", {
    data: function() {
        return {
            entered: "",
            autofocus: {
                type: Boolean,
                default: true,
            },
        };
    },
    props: {
        input_placeholder: String,
        input_data_type: String,
        reset_on_submit: {
            type: Boolean,
            default: true,
        },
    },
    methods: {
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
        },
    },

    template: `
  <v-form
      v-on:submit="search"
      :data-type="input_data_type"
      ref="form"
      class="searchform"
      >
    <v-text-field
      required v-model="entered"
      :placeholder="input_placeholder"
      :autofocus="autofocus ? 'autofocus' : null"
      />
  </v-form>
  `,
});
