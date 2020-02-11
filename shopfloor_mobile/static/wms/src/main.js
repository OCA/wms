//import searchbar from 'components/searchbar/searchbar.js'

import {Config} from './services/config.js'
import {Storage} from './services/storage.js'

const NotFound = { template: '<p>Page not found</p>' }
const Home = { template: '<home-page v-bind:routes="routes"></home-page>', props: {routes:"myroutes"}} // { props: {routes: AllRoutes} }}
const LoginPage = { template: '<login-page></login-page>' }
const ScanAnything = { template: '<scan-anything></scan-anything>' }

const ScenarioTemplate = {
   single_pack_putaway: {template: "<single-pack-putaway></single-pack-putaway>"},
   single_pack_transfer: {template: "<single-pack-transfer></single-pack-transfer>"},
}

var AppConfig = new Config()

class Routes {
    static get(path) {
        // support demo mode via hash eg: `#demo/single_pack_putaway`
        path = path.replace('demo/', '')
        if (path == '') {
            return Home
        } else if (path == 'scananything'){
            return ScanAnything
        } else {
            var menu_items = AppConfig.get('menus')
            for (var idx in menu_items) {
                if (menu_items[idx]['process_code'] == path) {
                    return ScenarioTemplate[menu_items[idx]['process_code']]
                }
            }
            return NotFound;
        }
    }
}

if ( Storage.apikey ) {
    AppConfig.load()
}

const vuetify_themes = {
    light: {
        primary: '#491966',
        secondary: '#424242',
        accent: '#82B1FF',
        error: '#FF5252',
        info: '#2196F3',
        success: '#4CAF50',
        warning: '#FFC107',
    }
}

var app = new Vue({
    el: '#app',
    vuetify: new Vuetify({
        // FIXME: has no effect
        // theme: {
        //     themes: vuetify_themes
        // }
    }),
    data: {
        currentRoute: window.location.hash.slice(1),
        demo_mode: false,
        config: AppConfig,
    },
    computed: {
        ViewComponent () {
            if (this.config.authenticated) {
                // TMP hack to be able to pass around params via querystring.
                // We'll use proper routing later.
                return Routes.get(this.currentRoute.split('?')[0]);
            } else {
                return LoginPage;
            }
        }
    },
    created: function () {
        this.demo_mode = window.location.hash.includes('demo')
    },
    render (h) { return h(this.ViewComponent) },

})

window.addEventListener('popstate', (e) => {
    // Using the hash of the url for navigation
    // To use url fragment we need a proper server in the backend
    app.currentRoute = window.location.hash.slice(1)
});
