export var Profile = Vue.component("profile", {
    data: function() {
        return {
            current_profile_id: this.$root.profile.id,
            profile_selected: false,
            user_notification: {
                message: "Profile updated",
                message_type: "info",
            },
        };
    },
    computed: {
        foo: function() {
            console.log("foo");
        },
    },
    template: `
        <Screen title="Select profile" :klass="'select-profile'">
            <template v-slot:header>
                <user-information
                    v-if="profile_selected"
                    v-bind:info="user_notification"
                    />
            </template>
            <manual-select
                :records="$root.config.data.profiles"
                :options="{initValue: this.$root.profile.id}"
                v-on:select="on_select"
                />
        </Screen>
    `,
    methods: {
        on_select: function(selected) {
            const self = this;
            // FIXME
            this.$root.trigger("state:change", "");
            this.$root.trigger("profile:selected", selected);
            this.profile_selected = true;
            setTimeout(function() {
                self.$root.$router.back();
            }, 2000);
        },
    },
});
