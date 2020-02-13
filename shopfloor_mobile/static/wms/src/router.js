const Home = { template: '<home-page v-bind:routes="routes"></home-page>', props: {routes:"myroutes"}} // { props: {routes: AllRoutes} }}
const Foo = { template: '<div>foo</div>' }
const Bar = { template: '<div>Bar</div>' }
const NotFound = { template: '<div>Lost in the scanner app.</div>' }

import {ScanAnything} from "./scenario/scan_anything.js";
import {LoginPage} from './loginpage.js'

const routes = [
  { path: '/foo', component: Foo },
  { path: '/bar', component: Bar },
  { path: '/', component: Home, name: 'home'},
  { path: '/login', component: LoginPage, name: 'login'},
  { path: '/scananything/:codebar?', component: ScanAnything, name: 'scananything' },
  // TODO Fix this it needs to be the last route, but I think it is not anymore with the dynamic one added.
  // { path: '*', component: NotFound },
]

const router = new VueRouter({
    routes: routes,
})
router.beforeEach(async (to, from, next) => {
    await Vue.nextTick()
    if (!router.app.config.authenticated && to.name!='login'){
        next('login')
    } else {
        next()
    }
})

export {router};
