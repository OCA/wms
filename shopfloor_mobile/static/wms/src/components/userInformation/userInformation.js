/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Thierry Ducrest <thierry.ducrest@camptocamp.com>
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

/* eslint-disable strict */
Vue.component("user-information", {
    props: ["message"],
    template: `
    <v-alert :type="alert_type" tile>
        <p v-for="line in message_lines" v-if="line" v-text="line"/>
        <p v-if="support_url">
            <a :href="support_url" v-text="message.support_url_text" />
        </p>
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
        support_url: function() {
            return _.result(this.message, "support_url", "");
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
