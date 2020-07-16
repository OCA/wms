export var HomePage = Vue.component("home-page", {
    computed: {
        navigation() {
            return this.$root.appmenu.menus;
        },
    },
    methods: {
        nuke_data_and_reload: function() {
            // Force reload config (loads profiles)
            this.$root.loadConfig(true);
            // Enforce 1st profile
            const selected_profile = _.head(this.$root.appconfig.profiles);
            this.$root.trigger("profile:selected", selected_profile, true);
            // Reload page
            location.reload();
        },
    },
    props: ["routes"],
    template: `
        <Screen :screen_info="{title: $t('screen.home.title'), klass: 'home'}" :show-menu="false">
            <v-list v-if="$root.has_profile">
                <nav-items :navigation="navigation"/>
            </v-list>

            <v-alert tile class="mt10" color="warning" v-if="$root.demo_mode">DEMO MODE ON</v-alert>
            <div class="button-list button-vertical-list full" v-if="$root.demo_mode">
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-action action="cancel" @click="nuke_data_and_reload()">Force reload data and refresh</btn-action>
                    </v-col>
                </v-row>
            </div>
        </Screen>
    `,
});
