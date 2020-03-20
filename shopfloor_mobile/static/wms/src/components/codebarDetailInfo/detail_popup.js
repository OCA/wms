import {Odoo, OdooMocked} from "../../services/odoo.js";

export var detailPopup = Vue.component("detail-popup", {
    mounted: function() {
        const odoo_params = {
            process_id: 99,
            process_menu_id: 99,
            usage: "scan_anything",
            debug: this.$root.demo_mode,
        };
        if (this.$root.demo_mode) {
            this.$root.loadJS("src/demo/demo." + this.usage + ".js", this.usage);
            this.odoo = new OdooMocked(odoo_params);
        } else {
            this.odoo = new Odoo(odoo_params);
        }
        this.getData(this.barcode);
    },
    methods: {
        getData: function(codebar) {
            this.odoo.scan_anything(codebar).then(result => {
                this.currentData = result.data;
            });
        },
        urlChanged: function(barcode) {
            // Raises a warning from Vue, but it is the way it should work
            this.barcode = barcode;
        },
    },
    data: function() {
        return {
            usage: "scan_anything",
            currentData: {},
        };
    },
    watch: {
        barcode: function(val) {
            this.getData(val);
        },
    },
    props: ["barcode"],
    template: `
    <div>
        <h3>Info {{ currentData.type}} : {{ currentData.barcode }}</h3>
        <hr>
        <detail-location :locationDetail="this.currentData.detail_info" v-if="currentData.type=='location'" v-on:url-change="urlChanged"></detail-location>
        <detail-product :productDetail="this.currentData.detail_info" v-if="currentData.type=='product'" v-on:url-change="urlChanged"></detail-product>
        <detail-pack :packDetail="this.currentData.detail_info" v-if="currentData.type=='pack'" v-on:url-change="urlChanged"></detail-pack>

    </div>
    `,
});
