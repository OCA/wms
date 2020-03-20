Vue.component("user-information", {
    props: ["info"],
    template: `
    <v-alert :type="alert_type" tile>
    {{ info.message }}
    </v-alert>
    `,
    computed: {
        alert_type: function() {
            return this.info.message_type;
        },
    },
});
