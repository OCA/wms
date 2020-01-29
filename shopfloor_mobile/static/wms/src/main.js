//import searchbar from 'components/searchbar/searchbar.js'

import * as simple_putaway from './scenario/simple_putaway/simple_putaway.js'
import {Config} from './services/config.js'
import {Storage} from './services/storage.js'

const NotFound = { template: '<p>Page not found</p>' }
const Home = { template: '<home-page v-bind:routes="routes"></home-page>', props: {routes:"myroutes"}} // { props: {routes: AllRoutes} }}
const LoginPage = { template: '<login-page></login-page>' }

const ScenarioTemplate = {
   single_pack_putaway: {template: "<simple-pack-putaway></simple-pack-putaway>"},
   single_pack_transfer: {template: "<pallet-transfer></pallet-transfer>"},
}

var AppConfig = new Config()

class Routes {
    static get(path) {
        if (path == '') {
            return Home
        } else {
           var menus = AppConfig.get('menus')
           for (var idx in menus) {
                if (menus[idx]['hash'] == path) {
                    return ScenarioTemplate[menus[idx]['process']]
                }
            };
            return NotFound;
        }
    }
}

if ( Storage.apikey ) {
    AppConfig.load()
}

var app = new Vue({
    el: '#app',
    vuetify: new Vuetify(),
    data: {
        currentRoute: window.location.hash.slice(1),
        using_demo_url: false,
        config: AppConfig,
    },
    computed: {
        ViewComponent () {
            if (this.config.authenticated) {
                return Routes.get(this.currentRoute);
            } else {
                return LoginPage;
            }
        }
    },
    created: function () {
        this.using_demo_url = window.location.pathname.includes('demo')
    },
    render (h) { return h(this.ViewComponent) },

})

window.addEventListener('popstate', (e) => {
    // Using the hash of the url for navigation
    // To use url fragment we need a proper server in the backend
    app.currentRoute = window.location.hash.slice(1)
});

console.log(simple_putaway)
simple_putaway.simple_putaway()
