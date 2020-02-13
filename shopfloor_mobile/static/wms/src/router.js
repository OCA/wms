import {HomePage} from './homepage.js'
import {ScanAnything} from "./scenario/scan_anything.js";
import {LoginPage} from './loginpage.js'
// const NotFound = { template: '<div>Lost in the scanner app.</div>' }

const routes = [
  { path: '/', component: HomePage, name: 'home'},
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
