var loginpage = Vue.component('login-page', {
    data: function(){ return {
        'apikey': '',
    }},
    methods: {
        login: function() {
            // call odoo application load => set the result in the local storage in json

            if (this.apikey == '123') {
                this.$root.authenticated = true;
                this.$root.config.reset(this.apikey)
            } else {
                this.$root.authenticated = false;
                this.accessbagde = '';
            }
        }
    },
    template: `

    <form>
    <h1 class="text-center">WMS</h1>
  <div class="form-group">
    <input type="text" class="form-control" v-model="apikey" placeholder="Scan your access badge or fill your credential" autofocus>
  </div>
  <button type="button" class="btn btn-primary btn-block" v-on:click="login()">Login</button>
</form>



    `
});

