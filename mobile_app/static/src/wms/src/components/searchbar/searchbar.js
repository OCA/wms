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
  <form v-on:submit="search">
	  <input v-model="entered" :placeholder="placeholder" class="form-control form-control-lg mb-2" />
  </form>
  `
})
