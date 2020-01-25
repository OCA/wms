console.log('searchbar !');
var lookup =  {
      	"un": "oooooo",
      	"123": "[ic 231] Ice Cream", 
      };

var searchbar = Vue.component('searchbar', {
  data: function () {
    return {
      entered: '',
    }
  },
  props:['placeholder'],
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
    <v-text-field required v-model="entered" :placeholder="placeholder" ></v-text-field>
  </v-form>
  `
})
