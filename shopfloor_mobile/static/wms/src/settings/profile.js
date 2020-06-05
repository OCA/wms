export var Profile = Vue.component("profile", {
    data: function() {
        return {
            current_profile_id: this.$root.has_profile ? this.$root.profile.id : null,
            profile_selected: false,
            user_notif_updated: {
                body: "Profile updated",
                message_type: "info",
            },
        };
    },
    template: `
        <Screen :title="$t('screen.settings.profile.title')" :klass="'settings settings-profile'">
            <template v-slot:header>
                <!-- TODO: rely on global notification -->
                <user-information
                    v-if="profile_selected"
                    :message="user_notif_updated"
                    />
            </template>
            <manual-select
                :records="$root.profiles"
                :options="{initValue: current_profile_id, showActions: false}"
                v-on:select="on_select"
                />

            <div class="button-list button-vertical-list full">
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-back/>
                    </v-col>
                </v-row>
                <!-- FIXME: maybe not a good place here -->
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-action action="warn" @click="reset_data()">Reload config and menu</btn-action>
                    </v-col>
                </v-row>
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-action @click="logout()">Logout</btn-action>
                    </v-col>
                </v-row>
            </div>
        </Screen>
    `,
    methods: {
        on_select: function(selected) {
            const self = this;
            this.$root.trigger("profile:selected", selected, true);
            self.$root.$router.push({name: "home"});
        },
        logout: function() {
            this.$root.logout();
        },
        reset_data: function() {
            this.$root._clearConfig();
            this.$root._loadMenu();
            this.$root.$router.push({name: "home"});
        },
    },
});
