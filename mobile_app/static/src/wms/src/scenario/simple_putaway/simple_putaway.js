var odoo_service = {
	'scanPack': function (barcode) {
		console.log('ask odoo about barcode of pack', barcode);
		return Promise.resolve({ 'source': 'def', 'destination': 'abc', 'id': 1233232, 'name': 'PACK0001'});
	},
	'scanLocation': function (barcode) {
		if (barcode.indexOf('a') != -1) {
			return Promise.resolve(barcode);
		} else {
			return Promise.reject('Invalid Location');
		} 
	},
	'cancel': function (operation) {
		console.log('tell odoo to cancel the move', operation.id);
	},
	'validate': function(operation) {
		console.log('Validate the move ', operation.id, ' on location dest: ', operation.destination);
	}
}


var sp = Vue.component('simple-pack-putaway', {
	template: `<div>
	<h1>Simple Putaway</h1>
    <searchbar v-on:found="scanned" v-bind:hint="hint" v-bind:placeholder="scanTip">ici lasearch</searchbar>
    <div class="alert alert-danger error" v-if="error_msg">{{ error_msg }}</div>
    <operation-detail v-bind:operation="operation"></operation-detail>
    <div v-if="confirm_with">
    	<div style="color:red">Destination not expected</div>
    	<p>Do you confirm ? {{ confirm_with }} </p>
    	<form v-on:submit="do_confirm" v-on:reset="dont_confirm">
    		<input type="submit" value="Yes"></input>
    		<input type="reset" value="No"></input>
    	</form>
    </div>
    <form v-if="show_button" v-on:reset="reset" v-on:submit="submit">
    	<input type="reset" name="reset"></input>
    </form>
</div>`,
	data: function () {
		return {
			'hint': 'pack',
			'show_button': false,
			'operation': {},
			'error_msg': '',
			'confirm_with': null,
		};
	},
	computed: {
	  scanTip: function () {
		return this.hint == 'pack' ? 'Scan pack': 'Scan location'
	  }
	},
	methods: {
		scanned: function(barcode) {
			this.error_msg = ''
			if (this.hint == 'pack') {
				odoo_service.scanPack(barcode).then( (value) => {
					this.operation = value;
					this.hint = 'location';
					this.show_button = true;	
				});
			} else {
				odoo_service.scanLocation(barcode).then( (value) => {
					console.log(value, this.operation.destination );
					if (value == this.operation.destination) {
						this.submit();
					} else {
						this.confirm_with = value;
						this.show_button = false

					}
				}, (error) => {
					console.error(error);
					this.error_msg = error;
				});
			}
		},
		dont_confirm: function() {
			this.confirm_with = null;
			this.show_button = true;
		},
		do_confirm: function() {
			this.operation.destination = this.confirm_with;
			this.confirm_with = null;
			this.show_button = true;
			this.submit();
		},
		reset_view: function() {
			this.hint = 'pack';
			this.show_button = false;
			this.operation = {};
			this.error_msg = '';
			this.confirm_with = null;
		},
		reset: function (e) {
			console.log('on reest ');
			this.reset_view();
			odoo_service.cancel(this.operation);
		},
		submit: function (e) {
			odoo_service.validate(this.operation);
			this.reset_view();
			e && e.preventDefault();
		},
	}
});


export function simple_putaway () { return sp }
