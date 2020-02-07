//import searchbar from 'components/searchbar/searchbar.js'

import {router} from './router.js'
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
            let menu_items = AppConfig.get('menus')
            for (var idx in menu_items) {
                let item = menu_items[idx]
                if (item.process && item.process.code == path) {
                    return ScenarioTemplate[item.process.code]
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

const app = new Vue({
    router: router,
    vuetify: new Vuetify({
        // FIXME: has no effect
        // theme: {
        //     themes: vuetify_themes
        // }
    }),
    data: {
        demo_mode: false,
        config: AppConfig,
    },
    created: function () {
        this.demo_mode = window.location.hash.includes('demo')
        this.demo_mode = true;
    },

}).$mount('#app');
