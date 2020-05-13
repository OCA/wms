export var SettingsControlPanel = Vue.component("settings-control-panel", {
    data: function() {
        return {};
    },
    template: `
        <Screen :title="$t('screen.settings.home.title')" :klass="'settings settings-control-panel'">
            <div class="button-list button-vertical-list full">
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <v-btn @click="$router.push({'name': 'profile'})">
                            <v-icon>mdi-account-cog</v-icon>
                            <span>{{ $t("screen.settings.profile.name") }}</span>
                        </v-btn>
                    </v-col>
                </v-row>
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <v-btn @click="$router.push({'name': 'language'})">
                            <v-icon>mdi-flag</v-icon>
                            <span>{{ $t("screen.settings.language.name") }}</span>
                        </v-btn>
                    </v-col>
                </v-row>
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-back/>
                    </v-col>
                </v-row>
            </div>
        </Screen>
    `,
});
