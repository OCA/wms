import {Odoo, OdooMocked} from "../services/odoo.js";

export var ScanAnything = Vue.component("scan-anything", {
    template: `
        <Screen title="Scan Anything" :klass="'scan_anything'">
            <searchbar v-on:found="on_scan" :input_placeholder="search_input_placeholder"></searchbar>
            <detail-pack :packDetail="dataReceived.detail_info" v-if="dataReceived.type=='pack'"></detail-pack>
            <detail-product :productDetail="dataReceived.detail_info" v-if="dataReceived.type=='product'"></detail-product>
            <detail-location :locationDetail="dataReceived.detail_info" v-if="dataReceived.type=='location'" v-on:url-change="urlChanged"></detail-location>
            <detail-operation :operationDetail="dataReceived.detail_info" v-if="dataReceived.type=='operation'"></detail-operation>
            <reset-screen-button v-on:reset="on_reset" :show_reset_button="show_reset_button"></reset-screen-button>
            <btn-back v-if="showBackBtn" />
        </Screen>
    `,
    mounted() {
        const odoo_params = {
            process_id: 99,
            process_menu_id: 99,
            usage: this.usage,
            debug: this.$root.demo_mode,
        };
        if (this.$root.demo_mode) {
            this.$root.loadJS("src/demo/demo." + this.usage + ".js", this.usage);
            this.odoo = new OdooMocked(odoo_params);
        } else {
            this.odoo = new Odoo(odoo_params);
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
            this.odoo.scan_anything(codebar).then(result => {
                this.dataReceived = result.data || {};
            });
        },
        on_scan: function(scanned) {
            this.$router.push({
                name: "scananything",
                params: {codebar: scanned.text},
            });
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
    data: function() {
        return {
            usage: "scan_anything",
            dataReceived: {},
            search_input_placeholder: "Scan anything",
        };
    },
});
