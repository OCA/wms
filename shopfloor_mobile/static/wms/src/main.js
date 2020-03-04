import {router} from './router.js';
import {Config} from './services/config.js';
import {Storage} from './services/storage.js';
import {process_registry} from './services/process_registry.js';


var AppConfig = new Config();

if ( Storage.apikey ) {
    AppConfig.load().then(() => {
        // Adding the routes dynamically when received from ther server
        AppConfig.get('menus').forEach(function (item) {
            const registered = process_registry.get(item.process.code);
            if (registered) {
                app.$router.addRoutes([{
                    path: "/" + item.process.code,
                    component: process_registry.get(item.process.code),
                    props: {menuItem: item},
                }]);
            } else {
                // TODO: use NotFound component
                console.error("Cannot find process component for", item.process.code, item);
            }
        });
    });
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
    },
};


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
        this.demo_mode = window.location.pathname.includes('demo');
        if (this.demo_mode) {
            this.loadJS('src/demo/demo.core.js', 'demo_core');
        }
    },
    methods: {
        loadJS: function (url, script_id) {
            if (script_id && !document.getElementById(script_id)) {
                console.log('Load JS', url);
                var script = document.createElement('script');
                script.setAttribute('src', url);
                script.setAttribute('type', 'text/javascript');
                script.setAttribute('id', script_id);
                document.getElementsByTagName("head")[0].appendChild(script);
            }
        },
    },

}).$mount('#app');
