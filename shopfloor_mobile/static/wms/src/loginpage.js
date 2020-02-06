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
            Storage.apikey = this.apikey
            this.error = ""
            this.$root.config.load().catch((error) => {
              this.error = "Invalid API KEY"
          });

        }
    },
    template: `
    <Screen title="Login"
            klass="login"
            :show-menu="false"
      <v-form v-on:submit="login">
        <p v-if="error">{{ error }}</p>
        <v-text-field
          v-model="apikey"
          label="API Key"
          placeholder="Scan your access badge or fill your credential"
          autofocus></v-text-field>
        <v-btn type="submit"></v-btn>
      </v-form>
    </Screen>
    `
});

