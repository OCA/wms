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
            return this.$root.config.get("menus");
        },
        screen_css_class() {
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
    }),
    template: `
    <v-app :class="$root.demo_mode ? 'demo_mode': ''">
        <v-navigation-drawer
                v-model="drawer"
                app
                >
            <v-list>
                <nav-items :navigation="navigation"/>
                <v-list-item @click="$router.push({'name': 'home'})" link>
                    <v-list-item-content>
                        <v-list-item-title>Main menu</v-list-item-title>
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
        <v-content :class="screen_css_class">
            <div class="header" v-if="$slots.header">
                <slot name="header">Optional header - no content</slot>
            </div>
            <v-container>
                <div class="main-content">
                    <slot>No content provided</slot>
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
    },
    template: `
    <div>
        <v-list-item
            v-for="item in navigation"
            :key="item.id"
            :href="'#/' + item.process.code"
            link
            >
            <v-list-item-content>
                <v-list-item-title>
                    {{ item.name }}
                </v-list-item-title>
                <v-list-item-subtitle>
                    <!-- TODO: hide this w/ v-if="$root.demo_mode" -->
                    <small class="warning">Process: {{ item.process.code }}</small>
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
