/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Thierry Ducrest <thierry.ducrest@camptocamp.com>
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */
import {HomePage} from "./homepage.js";
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
    // TODO Fix this it needs to be the last route, but I think it is not anymore with the dynamic one added.
    // { path: '*', component: NotFound },
];
let registered = [];
_.forEach(process_registry.all(), function(process, key) {
    routes.push({
        name: process.key,
        path: process.path,
        component: process.component,
    });
    registered.push(key);
});
if (registered.length)
    console.log("Registered component routes:", registered.join(", "));

const router = new VueRouter({
    routes: routes,
});
router.beforeEach(async (to, from, next) => {
    await Vue.nextTick();
    if (!router.app.authenticated && to.name != "login" && !router.app.demo_mode) {
        next("login");
    }
    if (router.app.global_state_key && to.name != from.name) {
        // If we switch away from a process / scenario, we must reset global state.
        router.app.$emit("state:change", "");
    }
    next();
});

export {router};
