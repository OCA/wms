/* eslint-disable strict */
Vue.component("Screen", {
    props: {
        title: String,
        showMenu: {
            type: Boolean,
            default: true,
        },
        klass: {
            type: String,
            default: "generic",
        },
    },
    computed: {
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
                "screen-" + this.klass,
                this.$slots.header ? "with-header" : "",
                this.$slots.footer ? "with-footer" : "",
            ].join(" ");
        },
    },
    data: () => ({
        drawer: null,
        missing_profile_msg: {
            message: "",
            message_type: "warning",
        },
    }),
    template: `
    <v-app :class="screen_app_class">
        <v-navigation-drawer
                v-model="drawer"
                app
                >
            <v-list>
                <v-btn icon class="close-menu" @click.stop="drawer = !drawer"><v-icon>mdi-close</v-icon></v-btn>
                <nav-items :navigation="navigation"/>
                <v-list-item @click="$router.push({'name': 'home'})" link>
                    <v-list-item-content>
                        <v-list-item-title><v-icon>mdi-home</v-icon> Home</v-list-item-title>
                    </v-list-item-content>
                </v-list-item>
            </v-list>
        </v-navigation-drawer>
        <v-app-bar
                color="#491966"
                dark
                flat
                app
                dense
                >
            <v-app-bar-nav-icon @click.stop="drawer = !drawer" v-if="showMenu" />
            <v-toolbar-title>{{ title }}</v-toolbar-title>
            <v-spacer></v-spacer>
            <app-bar-actions />
        </v-app-bar>
        <v-content :class="screen_content_class">
            <div class="header" v-if="$slots.header">
                <slot name="header">Optional header - no content</slot>
            </div>

            <v-alert type="warning" tile v-if="!this.$root.has_profile && this.$route.name!='profile'">
                <p>Profile not configured yet. Please select one.</p>
            </v-alert>

            <v-container>
                <div class="main-content">
                    <slot>No content provided or profile not configured.</slot>
                </div>
            </v-container>
            <!-- TODO: use flexbox to put it always at the bottom -->
            <div class="footer" v-if="$slots.footer">
                <slot name="footer">Optional footer - no content</slot>
            </div>
            <div class="loading" v-if="$root.loading">
                Loading...
                <!-- TODO: show a spinner -->
            </div>
        </v-content>
    </v-app>
    `,
});

Vue.component("nav-items", {
    props: {
        navigation: Array,
    },
    // FIXME: the menu click changes the route in the address bar but it does not reload the screen
    // if the route name is the same but w/ different menu_id. WTF????
    template: `
    <div>
        <v-list-item
            v-for="item in navigation"
            :key="item.id"
            :to="{name: item.process.code, params: {menu_id: item.id, state: 'start'}}"
            link
            >
            <v-list-item-content>
                <v-list-item-title>
                    {{ item.name }}
                </v-list-item-title>
                <v-list-item-subtitle>
                    <small class="font-weight-light">Process: {{ item.process.code }}</small>
                </v-list-item-subtitle>
            </v-list-item-content>
        </v-list-item>
    </div>
    `,
});

Vue.component("app-bar-actions", {
    template: `
    <div>
        <v-btn icon @click="$router.push({'name': 'scananything'})" :disabled="this.$route.name=='scananything'">
            <v-icon >mdi-magnify</v-icon>
        </v-btn>

        <v-btn icon @click="$router.push({'name': 'profile'})" :disabled="this.$route.name=='profile'">
            <v-icon >mdi-account-cog</v-icon>
        </v-btn>
    </div>
    `,
});
