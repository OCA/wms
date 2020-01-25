var homepage = Vue.component('home-page', {
    computed: {
        navigation () {
            return this.$root.config.get('menus');
            }
        },
    props:['routes'],
    template: `
        <Screen>
            <v-navigation-drawer
            class="deep-purple accent-4"
            dark
            permanent
            >
            <v-list>
                <v-list-item
                    v-for="item in navigation"
                    :key="item.name"
                    link
                    >
                    <v-list-item-content>
                        <v-list-item-title>{{ item.name }}</v-list-item-title>
                    </v-list-item-content>
                </v-list-item>
            </v-list>

            </v-navigation-drawer>
            <div class="btn-group-vertical">
                <a v-for="nav in this.navigation" v-bind:href="nav.hash"
                class="btn btn-primary btn-lg btn-block">
                    <span>{{ nav.name }}</span>
                </a>
            </div>
            <div class="alert alert-warning text-center" v-if="this.$root.using_demo_url">Using demo url</div>
        </Screen>
    `
});
