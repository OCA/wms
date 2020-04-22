export var HomePage = Vue.component("home-page", {
    computed: {
        navigation() {
            return this.$root.config.get("menus");
        },
    },
    props: ["routes"],
    template: `
        <Screen
            title="Barcode scanner"
            klass="home"
            :show-menu="false"
            >
            <v-list>
                <nav-items :navigation="navigation"/>
            </v-list>

            <v-alert tile class="mt10" color="warning" v-if="$root.demo_mode">DEMO MODE ON</v-alert>
        </Screen>
    `,
});
