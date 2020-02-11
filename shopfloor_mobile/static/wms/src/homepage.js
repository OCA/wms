var homepage = Vue.component('home-page', {
    computed: {
        navigation () {
            return this.$root.config.get('menus')
            }
        },
    props:['routes'],
    methods: {
        make_menu_item_url (menu_item) {
            let url = menu_item['process_code'] + '?' + new URLSearchParams(menu_item).toString()
            if (this.$root.demo_mode)
                url = 'demo/' + url
            return url
        }
    },
    template: `
        <Screen
            title="Barcode scanner"
            klass="home"
            :show-menu="false"
            >
            <v-list>
                <v-list-item
                    v-for="item in navigation"
                    :key="item.name"
                    :href="'#' + make_menu_item_url(item)"
                    link
                    >
                    <v-list-item-content>
                        <v-list-item-title>{{ item.name }}</v-list-item-title>
                    </v-list-item-content>
                </v-list-item>
            </v-list>

            <v-alert class="mt10" color="warning" v-if="$root.demo_mode">DEMO MODE ON</v-alert>
        </Screen>
    `
});
