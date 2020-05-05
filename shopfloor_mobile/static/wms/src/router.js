import {HomePage} from "./homepage.js";
import {ScanAnything} from "./scenario/scan_anything.js";
import {Profile} from "./mgmt/profile.js";
import {LoginPage} from "./loginpage.js";
import {process_registry} from "./services/process_registry.js";
// Const NotFound = { template: '<div>Lost in the scanner app.</div>' }

// TODO: handle routes via registry
let routes = [
    {path: "/", component: HomePage, name: "home"},
    {path: "/login", component: LoginPage, name: "login"},
    {path: "/profile", component: Profile, name: "profile"},
    {
        path: "/scananything/:codebar?",
        component: ScanAnything,
        name: "scananything",
    },
    // TODO Fix this it needs to be the last route, but I think it is not anymore with the dynamic one added.
    // { path: '*', component: NotFound },
];
_.forEach(process_registry.all(), function(component, key) {
    routes.push({
        name: key,
        path: process_registry.make_route(key),
        component: component,
    });
    console.log("registered component route", key);
});

const router = new VueRouter({
    routes: routes,
});
router.beforeEach(async (to, from, next) => {
    await Vue.nextTick();
    if (!router.app.authenticated && to.name != "login" && !router.app.demo_mode) {
        next("login");
    }
    next();
});

export {router};
