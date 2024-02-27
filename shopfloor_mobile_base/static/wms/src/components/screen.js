/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */

import event_hub from "../services/event_hub.js";

/* eslint-disable strict */
Vue.component("Screen", {
    props: {
        screen_info: {
            type: Object,
            default: function () {
                return {};
            },
        },
    },
    computed: {
        info() {
            // Defining defaults for an Object property
            // works only if you don't pass the property at all.
            // If you pass only one key, you'll lose all defaults.
            const screen_info = _.defaults({}, this.$props.screen_info, {
                title: "",
                current_doc: {},
                current_doc_identifier: "",
                showMenu: true,
                noUserMessage: false,
                user_message: null,
                user_popup: null,
                klass: "generic",
            });
            screen_info.current_doc_identifier = _.result(
                screen_info,
                "current_doc.identifier"
            );
            return screen_info;
        },
        navigation() {
            return this.$root.getNav();
        },
        screen_app_class() {
            return [
                this.$root.is_authenticated() ? "authenticated" : "anonymous",
                this.$root.loading ? "loading" : "",
                this.$root.demo_mode ? "demo_mode" : "",
                "env-" + this.$root.app_info.running_env,
            ].join(" ");
        },
        screen_content_class() {
            return [
                "screen",
                "screen-" + this.info.klass,
                this.$slots.header ? "with-header" : "",
                this.$slots.footer ? "with-footer" : "",
            ].join(" ");
        },
        show_profile_not_ready() {
            return (
                this.$root.is_authenticated() &&
                this.$route.meta.requiresProfile &&
                !this.$root.has_profile &&
                this.$root.app_info.profile_required
            );
        },
    },
    data: () => ({
        drawer: null,
        missing_profile_msg: {
            body: "",
            message_type: "warning",
        },
        show_popup: false,
        show_message: false,
    }),
    mounted() {
        this.$watch(
            "drawer",
            (value) => {
                if (value) {
                    // Refresh menu items and their counters when the drawer is expanded
                    this.$root.loadMenu(true);
                }
                this._on_drawer_transition();
            },
            {immediate: true}
        );
        // Manage popup display by passed property
        this.$watch(
            "screen_info.user_popup",
            (value) => {
                this.show_popup = Boolean(value);
            },
            {immediate: true}
        );
        this.$watch(
            "screen_info.user_message",
            (value) => {
                this.show_message = !this.info.noUserMessage && !_.isEmpty(value);
            },
            {immediate: true}
        );
    },
    methods: {
        _on_drawer_transition: function () {
            if (this.drawer) {
                document.body.classList.add("with-open-drawer");
                document.body.classList.remove("with-closed-drawer");
            } else {
                document.body.classList.add("with-closed-drawer");
                document.body.classList.remove("with-open-drawer");
            }
            event_hub.$emit("app:drawer_transition", {
                root: this.$root,
                drawer_opened: this.drawer,
            });
        },
    },
    template: `
    <v-app :class="screen_app_class">
        <v-navigation-drawer
                v-model="drawer"
                app
                >
            <v-list>
                <nav-items :navigation="navigation" :show_full_info="false" />
                <nav-items-extra />
            </v-list>
            <template v-slot:append>
                <v-divider></v-divider>
                <user-session-detail />
            </template>
        </v-navigation-drawer>
        <v-app-bar
                color="primary"
                dark
                app
                dense
                :class="{'has-main-doc': !_.isEmpty(info.current_doc)}"
                >
            <v-app-bar-nav-icon @click.stop="drawer = !drawer" v-if="info.showMenu" />
            <v-toolbar-title v-if="info.title">
                <span>
                    {{ info.title }}
                </span>
            </v-toolbar-title>

            <v-spacer></v-spacer>
            <v-btn icon v-if="info.current_doc_identifier" @click="$router.push({'name': 'scan_anything', params: {identifier: info.current_doc_identifier}, query: {displayOnly: 1}})">
                <btn-info-icon color="'#fff'" />
            </v-btn>
            <app-bar-actions v-if="$root.is_authenticated()"/>
        </v-app-bar>
        <v-main :class="screen_content_class">

            <div class="notifications">
                <slot name="notifications">
                    <user-information
                        v-if="show_message"
                        :message="info.user_message"
                        />
                    <user-popup
                        v-if="show_popup"
                        :popup="info.user_popup"
                        :visible="show_popup"
                        v-on:close="show_popup = false"
                        />
                </slot>
            </div>
            <div class="header" v-if="$slots.header">
                <slot name="header"></slot>
            </div>

            <profile-not-ready v-if="show_profile_not_ready" />

            <v-container>
                <screen-loading :loading="$root.loading" />
                <div class="main-content">
                    <slot>
                        <span v-if="this.$root.has_profile">{{ $root.loading_msg }}</span>
                    </slot>
                </div>
            </v-container>
            <!-- TODO: use flexbox to put it always at the bottom -->
            <div class="footer" v-if="$slots.footer">
                <slot name="footer">Optional footer - no content</slot>
            </div>
        </v-main>
    </v-app>
    `,
});

Vue.component("nav-items", {
    props: {
        navigation: Object,
        show_full_info: {
            type: Boolean,
            default: true,
        },
    },
    // NOTE: activation via router won't work because
    // we can use the same route w/ several menu items.
    // Hence we match via menu id.
    template: `
    <div :class="$options._componentTag">
        <v-list-item
            v-for="item in navigation.app_nav"
            :key="'nav-item-' + item.id"
            :to="{name: item.scenario, params: {menu_id: item.id, state: 'init'}}"
            link
            :color="$route.params.menu_id == item.id ? 'v-item-active' : null"
            >
            <v-list-item-content>
                <nav-item-content :item="item" :show_full_info="show_full_info" />
            </v-list-item-content>
            <v-list-item-action>
                <nav-item-action :item="item" />
            </v-list-item-action>
        </v-list-item>
        <v-list-item
            v-for="item in navigation.extra_nav"
            :key="'nav-item-' + item.id"
            :to="{name: item.to.name, params: item.to.params}"
            link
            >
            <v-list-item-content>
                <nav-item-content :item="item" :show_full_info="false" />
            </v-list-item-content>
        </v-list-item>
    </v-btn>
    </div>
    `,
});

Vue.component("nav-item-content", {
    props: {
        item: {
            type: Object,
            default: function () {
                return {};
            },
        },
        show_full_info: {
            type: Boolean,
            default: true,
        },
        options: {
            type: Object,
            default: function () {
                return {};
            },
        },
    },
    // NOTE: activation via router won't work because we can use the same route w/ several menu items.
    // Hence we match via menu id.
    template: `
        <div :class="$options._componentTag">
            <v-list-item-title class="primary--text">
                {{ item.name }}
            </v-list-item-title>
            <v-list-item-subtitle v-if="show_full_info">
                <small class="font-weight-light"><strong>{{ $t('app.nav.scenario') }}</strong> {{ item.scenario }}</small>
            </v-list-item-subtitle>
        </div>
    `,
});

Vue.component("nav-item-action", {
    props: {
        item: {
            type: Object,
            default: function () {
                return {};
            },
        },
        options: {
            type: Object,
            default: function () {
                return {};
            },
        },
    },
    template: `
        <div :class="$options._componentTag">
        </div>
    `,
});

Vue.component("nav-items-extra", {
    methods: {
        navigation: function () {
            return [
                {
                    id: "home",
                    name: this.$t("screen.home.title"),
                    icon: "mdi-home",
                    route: "/",
                },
                {
                    id: "scan-anything",
                    name: this.$t("screen.scan_anything.title", {what: ""}),
                    icon: "mdi-magnify",
                    route: {name: "scan_anything"},
                },
                {
                    id: "settings",
                    name: this.$t("screen.settings.title"),
                    icon: "mdi-cog-outline",
                    route: {name: "settings"},
                },
            ];
        },
    },
    template: `
    <div :class="$options._componentTag">
        <v-list-item
            v-for="item in navigation()"
            :key="'nav-item-extra-' + item.id"
            :to="item.route"
            link
            active-class="'v-item-active"
            exact
            >
            <v-list-item-content>
                <v-list-item-title><v-icon>{{ item.icon }}</v-icon> {{ item.name}}</v-list-item-title>
            </v-list-item-content>
        </v-list-item>
    </div>
    `,
});

Vue.component("app-bar-actions", {
    template: `
    <div :class="$options._componentTag">
        <v-btn icon @click="$router.push({'name': 'scan_anything'})" :disabled="this.$route.name=='scan_anything'">
            <v-icon >mdi-magnify</v-icon>
        </v-btn>
    </div>
    `,
});

Vue.component("app-version-footer", {
    template: `
        <v-footer absolute padless>
            <v-col class="text-center font-weight-light" cols="12">
                <span class="version">{{ $t('screen.home.version') }}</span> <span class="version-number" v-text="$root.app_info.version" />
            </v-col>
        </v-footer>
    `,
});
