var homepage = Vue.component('home-page', {
    computed: {
        navigation () {
            return this.$root.config.get('menus')
            }
        },
    props:['routes'],
    template: `
        <Screen
            title="Barcode scanner"
            :show-menu="false"
            >
            <v-list class="deep-purple accent-4">
                <v-list-item
                    v-for="item in navigation"
                    :key="item.name"
                    :href="'#' + item.hash"
                    link
                    >
                    <v-list-item-content>
                        <v-list-item-title>{{ item.name }}</v-list-item-title>
                    </v-list-item-content>
                </v-list-item>
            </v-list>

            <div class="alert alert-warning text-center" v-if="this.$root.using_demo_url">Using demo url</div>
        </Screen>
    `
});
