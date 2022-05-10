/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Thierry Ducrest <thierry.ducrest@camptocamp.com>
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */
import {HomePage} from "./homepage.js";
import {SettingsControlPanel} from "./settings/settings.js";
import {LoginPage} from "./loginpage.js";
import {process_registry} from "./services/process_registry.js";
import {page_registry} from "./services/page_registry.js";
// Const NotFound = { template: '<div>Lost in the scanner app.</div>' }

// Used to redirect to the chosen custom home path
// when landing in the "/" route.
let _CUSTOM_HOME_PATH = "";

const routes = [
    {
        path: "/login",
        component: LoginPage,
        name: "login",
    },
    {
        path: "/settings",
        component: SettingsControlPanel,
        name: "settings",
        meta: {requiresAuth: true},
    },
    // TODO Fix this it needs to be the last route, but I think it is not anymore with the dynamic one added.
    // { path: '*', component: NotFound },
];
const default_home_route = {
    path: "/",
    component: HomePage,
    name: "home",
    meta: {requiresAuth: true, requiresProfile: true, isHomeRoute: true},
};

const register_routes = function (route_records) {
    const registered = [];
    _.forEach(route_records, function (process, key) {
        const route = {
            name: process.key,
            component: process.component,
            path: process.route.path,
            meta: process.route.meta || {},
        };
        if (_.isUndefined(route.meta.requiresAuth)) {
            // By default, unless explicitly specified, require auth
            route.meta.requiresAuth = true;
        }
        if (route.meta.isHomeRoute) {
            if (_CUSTOM_HOME_PATH) {
                console.warn(
                    "Another home route was already registered. Skipping: ",
                    route
                );
            } else {
                _CUSTOM_HOME_PATH = route.path;
                const home_route_redirect = {
                    path: "/",
                    redirect: (to) => {
                        return _CUSTOM_HOME_PATH;
                    },
                };
                routes.push(home_route_redirect);
            }
        }
        routes.push(route);
        registered.push(key);
    });
    if (registered.length)
        console.log("Registered component routes:", registered.join(", "));
};

register_routes(process_registry.all());
register_routes(page_registry.all());
if (!_CUSTOM_HOME_PATH) routes.push(default_home_route);

const router = new VueRouter({
    routes: routes,
});
router.beforeEach(async (to, from, next) => {
    await Vue.nextTick();
    if (
        !router.app.is_authenticated() &&
        to.meta.requiresAuth &&
        !router.app.demo_mode
    ) {
        next("login");
    } else {
        if (router.app.global_state_key && to.name != from.name) {
            // If we switch away from a process / scenario, we must reset global state.
            router.app.$emit("state:change", "");
        }
        next();
    }
});

export {router};
