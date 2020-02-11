import {router} from './router.js'
import {Config} from './services/config.js'
import {Storage} from './services/storage.js'

import {SinglePackPutAway} from './scenario/single_pack_putaway.js'
import {SinglePackTransfer} from './scenario/single_pack_transfer.js'
import {ClusterPicking} from './scenario/cluster_picking.js'

// TODO: we should have a registry to be able to plug new scenario from outside
const ScenarioTemplate = {
   single_pack_putaway: SinglePackPutAway,
   single_pack_transfer: SinglePackTransfer,
   cluster_picking: ClusterPicking,
}

var AppConfig = new Config()

if ( Storage.apikey ) {
    AppConfig.load().then(() => {
        // Adding the routes dynamically when received from ther server
        AppConfig.get('menus').forEach(function(item){
            console.dir(item)
            app.$router.addRoutes([{
                path: "/" + item.process.code,
                component: ScenarioTemplate[item.process.code],
                props: { menuItem: item}
            }])
        })
    })
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
        // TODO This need to be fixed so it is dynamic again
        this.demo_mode = true;
    },

}).$mount('#app');
