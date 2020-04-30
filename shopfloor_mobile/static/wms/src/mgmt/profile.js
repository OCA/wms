export var Profile = Vue.component("profile", {
    data: function() {
        return {
            current_profile_id: this.$root.has_profile ? this.$root.profile.id : null,
            profile_selected: false,
            user_notif_updated: {
                message: "Profile updated",
                message_type: "info",
            },
        };
    },
    template: `
        <Screen title="Select profile" :klass="'select-profile'">
            <template v-slot:header>
                <user-information
                    v-if="profile_selected"
                    v-bind:info="user_notif_updated"
                    />
            </template>
            <manual-select
                :records="$root.appconfig.profiles"
                :options="{initValue: current_profile_id}"
                v-on:select="on_select"
                />
            <!-- FIXME: maybe not a good place here -->
            <v-btn depressed x-large color="error" v-on:click="reset_data()">Reload config</v-btn>
            <v-btn depressed x-large color="warning" v-on:click="logout()">Logout</v-btn>
            </Screen>
    `,
    methods: {
        on_select: function(selected) {
            const self = this;
            this.$root.trigger("profile:selected", selected, true);
            this.profile_selected = true;
            setTimeout(function() {
                self.$root.$router.back();
            }, 2000);
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
