Vue.component('Screen', {
    props: {
        'title': String,
        'showMenu': {
            'type': Boolean,
            'default': true,
        },
        'klass': {
            'type': String,
            'default': 'generic',
        },
    },
    computed: {
        navigation () {
            return this.$root.config.get('menus');
        },
        screen_css_class () {
            return [
                'screen',
                'screen-' + this.klass,
                this.$slots.footer ? 'with-footer': '',
            ].join(' ');
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
                <v-list-item
                    v-for="item in navigation"
                    :key="item.name"
                    :href="'#/' + item.process.code"
                    link
                    >
                    <v-list-item-content>
                        <v-list-item-title>{{ item.name }}</v-list-item-title>
                    </v-list-item-content>
                </v-list-item>
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
                >
            <v-app-bar-nav-icon @click.stop="drawer = !drawer" v-if="showMenu" />

            <v-toolbar-title>{{ title }}</v-toolbar-title>
            <v-spacer></v-spacer>
            <v-btn icon @click="$router.push('scananything')">
                <v-icon >mdi-magnify</v-icon>
            </v-btn>
            <v-menu
                left
                bottom
                >
                <template v-slot:activator="{ on }">
                    <v-btn icon v-on="on">
                    <v-icon>mdi-dots-vertical</v-icon>
                    </v-btn>
                </template>

                <v-list>
                    <v-list-item
                    v-for="n in 5"
                    :key="n"
                    @click="() => {}"
                    >
                    <v-list-item-title>Option {{ n }}</v-list-item-title>
                    </v-list-item>
                </v-list>
            </v-menu>
        </v-app-bar>
        <v-content>
            <v-container>
                <div :class="screen_css_class">
                    <div class="main-content">
                        <slot>No content provided</slot>
                    </div>
                    <div class="footer" v-if="$slots.footer">
                        <slot name="footer">Optional footer - no content</slot>
                    </div>
                </div>
            </v-container>
        </v-content>
    </v-app>
    `,
});
