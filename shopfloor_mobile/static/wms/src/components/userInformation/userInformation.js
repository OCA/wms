/* eslint-disable strict */
Vue.component("user-information", {
    props: ["message"],
    template: `
    <v-alert :type="alert_type" tile>
        <p v-for="line in message_lines" v-if="line" v-text="line"/>
    </v-alert>
    `,
    computed: {
        alert_type: function() {
            return _.result(this.message, "message_type", "info");
        },
        message_lines: function() {
            const msg = _.result(this.message, "body");
            return msg ? msg.split("\n") : [];
        },
    },
});

Vue.component("user-popup", {
    props: {
        popup: Object,
        visible: {
            type: Boolean,
            default: true,
        },
    },
    computed: {
        dialog: {
            get: function() {
                return this.visible;
            },
            set: function(value) {
                if (!value) {
                    this.$emit("close");
                }
            },
        },
    },
    template: `
    <v-dialog v-model="dialog" fullscreen tile class="actions fullscreen popup text-center">
        <v-alert type="info" tile>
            <div class="popup-body">{{ popup.body }}</div>
            <div class="button-list button-vertical-list full">
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <v-btn x-large color="secondary" @click="dialog = false">{{ $t("btn.ok.title") }}</v-btn>
                    </v-col>
                </v-row>
            </div>
        </v-alert>
    </v-dialog>
    `,
});
