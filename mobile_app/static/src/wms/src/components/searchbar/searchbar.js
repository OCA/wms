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
  methods: {
  	search: function(e) {
  		e.preventDefault();
  		Promise.resolve(true).then( () => { //for async simulation
  			var result = lookup[this.entered];
  			console.log('odoo has answered', result);
  			this.$emit('found', result);  //talk to parent
  			this.reset();
  		});
  	},
  	reset: function () {
  		this.entered = '';
  	}
  },

  template: '<form v-on:submit="search"><input v-model="entered" placeholder="barcode here"> </form>'
})
