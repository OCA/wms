/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

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
            return this.$root.appmenu.menus;
        },
        screen_app_class() {
            return [
                this.$root.authenticated ? "authenticated" : "anonymous",
                this.$root.loading ? "loading" : "",
                this.$root.demo_mode ? "demo_mode" : "",
            ].join(" ");
        },
        screen_content_class() {
            return [
                "screen",
                "screen-" + this.info.klass,
                this.$slots.header ? "with-header" : "",
                this.$slots.footer ? "with-footer" : "",
                this.utils.colors.color_for("content_bg"),
            ].join(" ");
        },
        show_profile_not_ready() {
            return (
                this.$root.authenticated &&
                !this.$root.has_profile &&
                // TODO: Routes should have a metadata flag `profile_required` ?
                // to replace the following check.
                this.$route.name != "profile" &&
                this.$route.name != "settings" &&
                this.$route.name != "workstation"
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
                if (value)
                    // Refresh menu items and their counters when the drawer is expanded
                    this.$root.loadMenu(true);
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
                <v-list v-if="$root.user.id">
                    <v-list-item>
                        <v-list-item-avatar>
                            <v-avatar color="primary" size="36">
                                <v-icon dark>mdi-account-circle</v-icon>
                            </v-avatar>
                        </v-list-item-avatar>
                        <v-list-item-content>
                            <span v-text="$root.user.name" />
                        </v-list-item-content>
                    </v-list-item>
                </v-list>
            </template>
        </v-navigation-drawer>
        <v-app-bar
                color="#491966"
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
            <app-bar-actions v-if="$root.authenticated"/>
        </v-app-bar>
        <v-content :class="screen_content_class">

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

            <div class="profile-not-ready" v-if="show_profile_not_ready">
                <v-alert type="warning" tile>
                    <p>{{ $t('app.profile_not_configured') }}</p>
                </v-alert>
                <div class="button-list button-vertical-list full">
                    <v-row align="center">
                        <v-col class="text-center" cols="12">
                            <v-btn @click="$router.push({'name': 'profile'})">
                                <v-icon>mdi-account-cog</v-icon>
                                <span>{{ $t('app.profile_configure') }}</span>
                            </v-btn>
                        </v-col>
                        <v-col class="text-center" cols="12">
                            <v-btn @click="$router.push({'name': 'workstation'})">
                                <v-icon>mdi-account-cog-outline</v-icon>
                                <span>{{ $t('app.workstation_scan') }}</span>
                            </v-btn>
                        </v-col>
                    </v-row>
                </div>
            </div>

            <v-container>
                <screen-loading :loading="$root.loading" />
                <div class="main-content">
                    <slot>
                        <span v-if="this.$root.has_profile">{{ $t('app.loading') }}</span>
                    </slot>
                </div>
            </v-container>
            <!-- TODO: use flexbox to put it always at the bottom -->
            <div class="footer" v-if="$slots.footer">
                <slot name="footer">Optional footer - no content</slot>
            </div>
        </v-content>
    </v-app>
    `,
});

Vue.component("nav-items", {
    props: {
        navigation: Array,
        show_full_info: {
            type: Boolean,
            default: true,
        },
    },
    // NOTE: activation via router won't work because we can use the same route w/ several menu items.
    // Hence we match via menu id.
    template: `
    <div :class="$options._componentTag">
        <v-list-item
            v-for="item in navigation"
            :key="'nav-item-' + item.id"
            :to="{name: item.scenario, params: {menu_id: item.id, state: 'init'}}"
            link
            active-class="'v-item-active"
            :color="$route.params.menu_id == item.id ? 'v-item-active' : null"
            >
            <v-list-item-content>
                <v-list-item-title class="primary--text">
                    {{ item.name }}
                </v-list-item-title>
                <v-list-item-subtitle v-if="show_full_info">
                    <small class="font-weight-light"><strong>{{ $t('app.nav.scenario') }}</strong> {{ item.scenario }}</small>
                    <br />
                    <small class="font-weight-light text-wrap pr-2">
                        <strong>{{ $t('app.nav.op_types') }}</strong>
                        <span v-for="(pt, index) in item.picking_types"
                              :key="'pt-' + item.id + '-' + pt.id"
                              >{{ pt.name }}<span v-if="index != (item.picking_types.length - 1)">,</span>
                        </span>
                    </small>
                </v-list-item-subtitle>
            </v-list-item-content>
            <v-list-item-action v-if="item.lines_count">
                <div class="pa-4 secondary text-no-wrap rounded-pill">
                    {{ $t('misc.lines_count', item) }}
                </div>
            </v-list-item-action>
        </v-list-item>
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
                    route: {name: "home"},
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
