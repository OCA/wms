export var LoginPage = Vue.component("login-page", {
    data: function() {
        return {
            apikey: "",
            error: "",
        };
    },
    methods: {
        login: function(evt) {
            evt.preventDefault();
            // Call odoo application load => set the result in the local storage in json
            this.error = "";
            this.$root.apikey = this.apikey;
            this.$root
                ._loadConfig()
                .catch(error => {
                    this.error = "Invalid API KEY";
                    this.$root.apikey = "";
                })
                .then(() => {
                    // TODO: shall we do this in $root._loadRoutes?
                    if (this.$root.authenticated) {
                        this.$router.push({name: "home"});
                    }
                });
        },
    },
    template: `
    <Screen title="Login"
            klass="login"
            :show-menu="false"

        <v-container>
            <v-row
                align="center"
                justify="center">
                <v-col cols="12" sm="8" md="4">
                    <div class="login-wrapper">
                        <v-form v-on:submit="login">
                            <p v-if="error">{{ error }}</p>
                            <v-text-field
                                v-model="apikey"
                                label="API Key"
                                placeholder="Scan your access badge or fill your credential"
                                autofocus></v-text-field>
                            <v-btn color="success" type="submit">Submit</v-btn>
                        </v-form>
                    </div>
                </v-col>
            </v-row>
        </v-container>
    </Screen>
    `,
});
