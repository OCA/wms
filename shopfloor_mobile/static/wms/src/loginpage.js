import {Storage} from './services/storage.js'

Vue.component('login-page', {
    data: function(){ return {
        'apikey': '72B044F7AC780DAC',
        'error': '',
    }},
    methods: {
        login: function(evt) {
            evt.preventDefault();
            // call odoo application load => set the result in the local storage in json
            Storage.apikey = this.apikey;
            this.error = "";
            this.$root.config.load().catch((error) => {
              this.error = "Invalid API KEY";
          });

        }
    },
    template: `

    <form v-on:submit="login">
    <h1 class="text-center">WMS</h1>
  <div class="form-group">

    <p>{{ error }}</p>
    <input type="text" class="form-control" v-model="apikey" placeholder="Scan your access badge or fill your credential" autofocus>
  </div>
  <input type="submit" class="btn btn-primary btn-block" >Login</button>
</form>
    `
});

