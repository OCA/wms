//import searchbar from 'components/searchbar/searchbar.js'

import * as simple_putaway from './scenario/simple_putaway/simple_putaway.js'

const NotFound = { template: '<p>Page not found</p>' }
const Home = { template: '<home-page v-bind:routes="routes"></home-page>', props: {routes:"myroutes"}} // { props: {routes: AllRoutes} }}
const PutAway = { template: '<simple-pack-putaway></simple-pack-putaway>' }
const PalletTransfer = { template: '<pallet-transfer></pallet-transfer>' }

const Routes = {
    '': Home,
    'putaway': PutAway,
    'pallettransfer': PalletTransfer,
}

var app = new Vue({
    el: '#app',
    data: {
        currentRoute: '',
    },
    computed: {
        ViewComponent () {
            return Routes[this.currentRoute] || NotFound
        }
    },
    render (h) { return h(this.ViewComponent) }

})

window.addEventListener('popstate', (e) => {
    // Using the hash of the url for navigation
    // To use url fragment we need a proper server in the backend
    app.currentRoute = window.location.hash.slice(1);
});

console.log(simple_putaway);
simple_putaway.simple_putaway();
