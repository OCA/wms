
var odoo_service = {
    'scan_pack': function (barcode) {
        console.log('ask odoo about barcode of pack', barcode.pack);
        return Promise.resolve({ 'source': 'def', 'destination': 'abc', 'id': 1233232, 'name': 'PACK0001', 'barcode': barcode.pack});
    },
}

var pt = Vue.component('pallet-transfer', {
    template: `
        <div>
        <h1><a href="#" class="btn btn-large btn-outline-secondary" style="margin-right:10px;">&lt;</a>Pallet Transfer</h1>
        {{ current_state }}
        <searchbar v-on:found="scanned" v-bind:hint="hint" v-bind:placeholder="scanTip">ici lasearch</searchbar>
        <user-information v-if="user_notification.message" v-bind:message="user_notification.message" v-bind:message_type="user_notification.message_type"></user-information>
        <user-confirmation v-if="current_state=='confirmPallet'" v-on:user-confirmation="onUserConfirmation" v-bind:title="user_confirmation.title" v-bind:question="user_confirmation.question"></user-confirmation>
    </div>
    `,
    data: function () {
        return {
            'user_confirmation': {
                'title': 'Pallet looks good.',
                'question': 'Is that the goood one?',
            },
            'user_notification': {
                'message': '',
                'message_type': '',
            },
            'hint': 'pallet',
            'operation': {},
            // 'error_msg': '',
            'current_state': 'getPallet',
            'state': {
                'getPallet': {
                    enter: () => {
                        this.hint = 'pallet';
                    },
                    on_scan: (scanned) => {
                        this.go_state(
                            'confirmPallet',
                            odoo_service.scan_pack({
                                'pack': scanned
                            })
                        );
                    },
                },
                'confirmPallet': {
                    enter: () => {
                    },
                    on_scan: (scanned) => {
                    },
                    on_answer: (answer) => {
                        if (answer == 'yes'){
                            this.go_state('getLocation');
                        } else {
                            this.go_state('getPallet');
                        }
                    },
                },
                'getLocation': {
                    enter: () => {
                        this.hint = 'location';
                    },
                    on_scan: (scanned) => {
                        this.go_state(
                            'transferDone',
                        );
                    },
                },
                'transferDone': {
                    enter: () => {
                        this.user_notification.message = "Good job!";
                        this.user_notification.message_type = "success";
                        this.go_state('getPallet');
                    }
                },
                // 'waitscan_pack': {
                //     success: (result) => {
                //         this.operation = result;
                //         this.go_state('operationSet');
                //     },
                //     'error': (result) => {
                //         console.error('no operation found');
                //         this.go_state('init');
                //     }
                // },
            }
        };
    },
    methods: {
        onUserConfirmation: function(answer){
            this.state[this.current_state].on_answer(answer);
        },
        scanned: function(barcode) {
            this.user_notification.message = "";
            this.state[this.current_state].on_scan(barcode);
        },
        go_state: function(state, promise) {
            if (this.state[this.current_state].exit)
                this.state[this.current_state].exit();
            this.current_state = state;
            if (promise) {
                promise.then(
                    this.state[state].success,
                    this.state[state].error,
                );
            } else {
                this.state[state].enter();
            }
        },
    },
    computed: {
      scanTip: function () {
        return 'Scan ' + this.hint;
      }
    },
});


export function pallet_transfer () { return pt }
