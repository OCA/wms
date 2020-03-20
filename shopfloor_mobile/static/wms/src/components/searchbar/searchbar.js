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
    props: ["input_placeholder", "input_data_type"],
    methods: {
        search: function(e) {
            e.preventDefault();
            this.$emit("found", {
                text: this.entered,
                type: e.target.dataset.type,
            }); // Talk to parent
            this.reset();
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
      >
    <v-text-field
      required v-model="entered"
      :placeholder="input_placeholder"
      :autofocus="autofocus ? 'autofocus' : null"
      />
  </v-form>
  `,
});
