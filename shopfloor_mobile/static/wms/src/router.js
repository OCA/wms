import {HomePage} from "./homepage.js";
import {ScanAnything} from "./scenario/scan_anything.js";
import {SettingsControlPanel} from "./settings/settings.js";
import {Profile} from "./settings/profile.js";
import {Language} from "./settings/language.js";
import {LoginPage} from "./loginpage.js";
import {process_registry} from "./services/process_registry.js";
// Const NotFound = { template: '<div>Lost in the scanner app.</div>' }

// TODO: handle routes via registry
let routes = [
    {path: "/", component: HomePage, name: "home"},
    {path: "/login", component: LoginPage, name: "login"},
    {path: "/settings", component: SettingsControlPanel, name: "settings"},
    {path: "/profile", component: Profile, name: "profile"},
    {path: "/language", component: Language, name: "language"},
    {
        path: "/scananything/:identifier?",
        component: ScanAnything,
        name: "scananything",
    },
    // TODO Fix this it needs to be the last route, but I think it is not anymore with the dynamic one added.
    // { path: '*', component: NotFound },
];
let registered = [];
_.forEach(process_registry.all(), function(component, key) {
    routes.push({
        name: key,
        path: process_registry.make_route(key),
        component: component,
    });
    registered.push(key);
});
if (registered.length)
    console.log("Registered component routes:", registered.join(", "));

const router = new VueRouter({
    routes: routes,
});
router.beforeEach(async (to, from, next) => {
    // TODO: if we switch from one scenario to another we should flush the storage of the previous one
    await Vue.nextTick();
    if (!router.app.authenticated && to.name != "login" && !router.app.demo_mode) {
        next("login");
    }
    next();
});

export {router};
