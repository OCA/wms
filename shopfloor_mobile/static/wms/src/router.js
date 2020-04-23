import {HomePage} from "./homepage.js";
import {ScanAnything} from "./scenario/scan_anything.js";
import {Profile} from "./mgmt/profile.js";
import {LoginPage} from "./loginpage.js";
// Const NotFound = { template: '<div>Lost in the scanner app.</div>' }

// TODO: handle routes via registry
const routes = [
    {path: "/", component: HomePage, name: "home"},
    {path: "/login", component: LoginPage, name: "login"},
    {path: "/profile", component: Profile, name: "profile"},
    {
        path: "/scananything/:codebar?",
        component: ScanAnything,
        name: "scananything",
    },
    {
        path: "/scananything/:codebar?",
        component: ScanAnything,
        name: "scananything",
    },
    // TODO Fix this it needs to be the last route, but I think it is not anymore with the dynamic one added.
    // { path: '*', component: NotFound },
];

const router = new VueRouter({
    routes: routes,
});
router.beforeEach(async (to, from, next) => {
    await Vue.nextTick();
    if (!router.app.authenticated && to.name != "login" && !router.app.demo_mode) {
        next("login");
    } else {
        next();
    }
});

export {router};
