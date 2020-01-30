Vue.component('searchbar', {
  data: function () {
    return {
      entered: '',
    }
  },
  props:['input_placeholder'],
  methods: {
  	search: function(e,) {
  		e.preventDefault();
		this.$emit('found', this.entered);  //talk to parent
		this.reset();
  	},
  	reset: function () {
  		this.entered = '';
  	}
  },

  template: `
  <v-form
      v-on:submit="search"
      ref="form"
      >
    <v-text-field required v-model="entered" :placeholder="input_placeholder" ></v-text-field>
  </v-form>
  `
})
