//import searchbar from 'components/searchbar/searchbar.js'

var vue = new Vue({
	el: '#app',
	data: {
		'txt': 'search something'
	},
	methods: {
		showFound: function(fff) {
			console.log('found: ', fff);
			this.txt = fff;
		}
	}
})
