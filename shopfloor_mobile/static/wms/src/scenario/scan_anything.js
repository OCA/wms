export var ScanAnything = Vue.component("scan-anything", {
    template: `
        <Screen title="Scan Anything" :klass="'scan_anything'">
            <searchbar v-on:found="on_scan" :input_placeholder="search_input_placeholder"></searchbar>
            <component
                :is="detail_component_name()"
                :record="dataReceived.detail_info"
                />
            <reset-screen-button v-on:reset="on_reset" :show_reset_button="show_reset_button"></reset-screen-button>
            <btn-back v-if="showBackBtn" />
        </Screen>
    `,
    data: function() {
        return {
            usage: "scan_anything",
            dataReceived: {},
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
        if (this.$route.params.codebar) {
            this.getData(this.$route.params.codebar);
        }
    },
    beforeRouteUpdate(to, from, next) {
        if (to.params.codebar) {
            this.getData(to.params.codebar);
        } else {
            this.dataReceived = {};
        }
        next();
    },
    methods: {
        on_reset: function(e) {
            this.dataReceived = {};
            this.$router.push({name: "scananything", params: {codebar: undefined}});
        },
        urlChanged: function(codebar) {
            // Change the route on when more info clicked in children
            const query = {};
            if ("codebar" in this.$route.params) {
                query.childOf = this.$route.params.codebar;
            }
            this.$router.push({
                name: "scananything",
                params: {codebar: codebar},
                query: query,
            });
        },
        getData: function(codebar) {
            this.odoo.call(codebar).then(result => {
                this.dataReceived = result.data || {};
            });
        },
        on_scan: function(scanned) {
            this.$router.push({
                name: "scananything",
                params: {codebar: scanned.text},
            });
        },
        detail_component_name() {
            if (_.isEmpty(this.dataReceived)) {
                return null;
            }
            const name = "detail-" + this.dataReceived.type;
            if (!name in Vue.options.components) {
                console.error("Detail component ", name, " not found.");
                return null;
            }
            return name;
        },
    },
    computed: {
        showBackBtn: function() {
            return "childOf" in this.$route.query;
        },
        show_reset_button: function() {
            return !_.isEmpty(this.dataReceived);
        },
    },
});
