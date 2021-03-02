/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Thierry Ducrest <thierry.ducrest@camptocamp.com>
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {process_registry} from "../services/process_registry.js";

const ScanAnything = {
    template: `
        <Screen :screen_info="screen_info">
            <searchbar
                v-if="!displayOnly"
                v-on:found="on_scan"
                :input_placeholder="search_input_placeholder"
                />
            <component
                :is="detail_component_name()"
                :record="scan_data.record"
                :options="{full_detail: true}"
                />
            <div class="button-list button-vertical-list full">
                <v-row align="center" v-if="showBackBtn">
                    <v-col class="text-center" cols="12">
                        <btn-back />
                    </v-col>
                </v-row>
                <v-row align="center" v-if="!displayOnly && showResetBtn">
                    <v-col class="text-center" cols="12">
                        <reset-screen-button v-on:reset="on_reset" :show_reset_button="showResetBtn"></reset-screen-button>
                    </v-col>
                </v-row>
            </div>
        </Screen>
    `,
    data: function() {
        return {
            usage: "scan_anything",
            scan_full_data: {},
            scan_data: {},
            scan_message: {},
            search_input_placeholder: this.$t("screen.scan_anything.scan_placeholder"),
        };
    },
    mounted() {
        const odoo_params = {
            usage: this.usage,
        };
        this.odoo = this.$root.getOdoo(odoo_params);
        if (this.$route.params.identifier) {
            this.getData(this.$route.params.identifier);
        }
    },
    beforeRouteUpdate(to, from, next) {
        if (to.params.identifier) {
            this.getData(to.params.identifier);
        } else {
            this.scan_data = {};
        }
        next();
    },
    methods: {
        on_reset: function(e) {
            this.scan_data = {};
            this.$router.push({name: "scan_anything", params: {identifier: undefined}});
        },
        getData: function(identifier) {
            this.odoo.call("scan", {identifier: identifier}).then(result => {
                this.scan_full_data = result || {};
                this.scan_data = result.data || {};
                this.scan_message = result.message || null;
            });
        },
        on_scan: function(scanned) {
            if (this.$route.params.identifier == scanned.text) {
                // scanned same resource, just reload
                this.getData(scanned.text);
            } else {
                this.$router.push({
                    name: "scan_anything",
                    params: {identifier: scanned.text},
                });
            }
        },
        detail_component_name() {
            if (_.isEmpty(this.scan_data)) {
                return null;
            }
            const name = "detail-" + this.scan_data.type;
            if (!name in Vue.options.components) {
                console.error("Detail component ", name, " not found.");
                return null;
            }
            return name;
        },
    },
    computed: {
        screen_info: function() {
            return {
                title: this.screen_title,
                klass: "scan-anything",
                user_message: this.scan_message,
            };
        },
        screen_title: function() {
            return this.$t("screen.scan_anything.title", {
                what: this.$route.params.identifier,
            });
        },
        displayOnly: function() {
            return this.$route.query.displayOnly;
        },
        showBackBtn: function() {
            return "childOf" in this.$route.query || this.displayOnly;
        },
        showResetBtn: function() {
            return !_.isEmpty(this.scan_data);
        },
    },
};

process_registry.add("scan_anything", ScanAnything, {
    path: "/scan_anything/:identifier?",
    meta: {
        profileRequired: false,
    },
});

export default ScanAnything;
