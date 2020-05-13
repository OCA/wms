export var ScanAnything = Vue.component("scan-anything", {
    template: `
        <Screen :title="screen_title" :klass="'scan_anything'">
            <template v-slot:header>
                <user-information
                    v-if="scan_message.length"
                    v-bind:info="scan_message"
                    />
            </template>
            <searchbar
                v-if="!displayOnly"
                v-on:found="on_scan"
                :input_placeholder="search_input_placeholder"
                />
            <component
                :is="detail_component_name()"
                :record="scan_data.record"
                :options="{on_url_change: on_url_change, full_detail: true}"
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
            search_input_placeholder: "Scan anything",
        };
    },
    mounted() {
        const odoo_params = {
            usage: this.usage,
        };
        this.odoo = this.$root.getOdoo(odoo_params);
        if (this.$root.demo_mode) {
            this.$root.loadJS("src/demo/demo." + this.usage + ".js", this.usage);
        }
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
            this.$router.push({name: "scananything", params: {identifier: undefined}});
        },
        on_url_change: function(identifier) {
            // Change the route on when more info clicked in children
            const query = {};
            if ("identifier" in this.$route.params) {
                query.childOf = this.$route.params.identifier;
            }
            this.$router.push({
                name: "scananything",
                params: {identifier: identifier},
                query: query,
            });
        },
        getData: function(identifier) {
            this.odoo.call("scan", {identifier: identifier}).then(result => {
                this.scan_full_data = result || {};
                this.scan_data = result.data || {};
                this.scan_message = result.message || {};
            });
        },
        on_scan: function(scanned) {
            this.$router.push({
                name: "scananything",
                params: {identifier: scanned.text},
            });
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
        displayOnly: function() {
            return this.$route.query.displayOnly;
        },
        showBackBtn: function() {
            return "childOf" in this.$route.query || this.displayOnly;
        },
        showResetBtn: function() {
            return !_.isEmpty(this.scan_data);
        },
        screen_title: function() {
            let title = "Scan anything";
            if (this.$route.params.identifier) {
                title = "Scanned: " + this.$route.params.identifier;
            }
            return title;
        },
    },
});
