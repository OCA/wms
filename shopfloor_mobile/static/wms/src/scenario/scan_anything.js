import {ScenarioBaseMixin} from "./mixins.js";

export var ScanAnything = Vue.component('scan-anything', {
    mixins: [ScenarioBaseMixin],
    template: `
        <Screen title="Scan Anything">
            <searchbar v-on:found="on_scan" :input_placeholder="search_input_placeholder"></searchbar>
            <user-information v-if="!need_confirmation && user_notification.message" v-bind:info="user_notification"></user-information>
            <detail-pack :packDetail="state.data" v-if="state.data.type=='pack'"></detail-pack>
            <detail-product :productDetail="this.state.data.detail_info" v-if="state.data.type=='product'"></detail-product>
            <detail-location :locationDetail="this.state.data.detail_info" v-if="state.data.type=='location'"></detail-location>
            <detail-operation :operationDetail="this.state.data.detail_info" v-if="state.data.type=='operation'"></detail-operation>
            <reset-screen-button v-on:reset="on_reset" :show_reset_button="show_reset_button"></reset-screen-button>
        </Screen>
    `,
    mounted () {
        if (this.$route.params["codebar"]){
            this.go_state(
                'wait_call',
                this.odoo.scan_anything(this.$route.params["codebar"])
            )
        }
    },
    beforeRouteUpdate (to, from, next) {
        this.go_state(this.initial_state_key)
        if (to.params["codebar"]){
            this.go_state(
                'wait_call',
                this.odoo.scan_anything(to.params["codebar"])
            )
        }
        next()
    },
    methods: {
        on_reset: function (e) {
            this.reset_notification()
            this.reset_erp_data('data')
            this.$router.push({ name: "scananything", params: {codebar: undefined}})
        },
    },
    data: function () {
        return {
            'usage': 'scan_anything',
            'show_reset_button': true,
            'initial_state_key': 'scan_something',
            'current_state_key': 'scan_something',
            'states': {
                'scan_something': {
                    enter: () => {
                        this.reset_erp_data('data')
                    },
                    on_scan: (scanned) => {
                        this.$router.push({
                            "name": "scananything",
                            params: {"codebar": scanned.text}
                        })
                    },
                    scan_placeholder: 'Scan anything...',
                },
                'wait_call': {
                    success: (result) => {
                        if (result.data != undefined)
                            this.set_erp_data('data', result.data)
                        this.go_state('show_detail_info')
                    },
                    error: (result) => {
                        this.go_state('scan_something')
                    },
                },
                'show_detail_info': {
                    enter: () => {
                        this.state.data.location_barcode = false
                    },
                    on_scan: (scanned) => {
                        this.state.data.location_barcode = scanned.text
                        this.$router.push({
                            "name": "scananything",
                            params: {"codebar": scanned.text}
                        })
                    },
                },
            }
        }
    },
})
