/* eslint-disable strict */
/* eslint-disable no-implicit-globals */
import {CheckoutPickingDetailListMixin} from "./mixins.js";

Vue.component("checkout-summary-detail", {
    mixins: [CheckoutPickingDetailListMixin],
    computed: {
        list_opts() {
            // Defining defaults for an Object property
            // works only if you don't pass the property at all.
            // If you pass only one key, you'll lose all defaults.
            const opts = _.defaults({}, this.$props.list_options, {
                showCounters: true,
                list_item_component: "checkout-summary-content",
                // list_item_action_component: "checkout-summary-content",
            });
            return opts;
        },
    },
});

Vue.component("checkout-summary-content", {
    props: {
        record: Object,
        options: Object,
        index: Number,
        count: Number,
    },
    template: `
    <div class="summary-content d-flex">
        <v-list-item-content :class="'justify-start ' + (record.key == 'no-pack'? 'no-pack' : 'has-pack' )">
            <v-expansion-panels v-if="record.key != 'no-pack' && record.records_by_pkg_type" flat>
                <v-expansion-panel v-for="pkg_type in record.records_by_pkg_type" :key="pkg_type.key"">
                    <v-expansion-panel-header>
                        <span class="item-counter">
                            <span>{{ index + 1 }} / {{ count }}</span>
                        </span>
                        {{ record.title }}
                    </v-expansion-panel-header>
                    <v-expansion-panel-content>
                        <strong class="pkg-type-name">{{ pkg_type.title }}</strong>
                        <edit-action :record="record.pack" :click_event="'pkg_change_type'" />
                        <checkout-summary-product-detail
                            v-for="(prod, i) in pkg_type.records"
                            :record="prod"
                            :index="i"
                            :count="pkg_type.records.length"
                            />
                    </v-expansion-panel-content>
                </v-expansion-panel>
            </v-expansion-panels>
            <div v-else v-for="(subrec, i) in record.records">
                <checkout-summary-product-detail :record="subrec" :index="index" :count="count" />
            </div>
        </v-list-item-content>
        <v-list-item-action v-if="record.key != 'no-pack'" class="justify-end">
            <checkout-summary-destroy-action :pack="record.pack" />
        </v-list-item-action>
    </div>
    `,
});

// TODO: split these actions out of checkout
//
Vue.component("checkout-summary-destroy-action", {
    props: ["pack"],
    data() {
        return {
            dialog: false,
        };
    },
    methods: {
        on_user_confirm: function(answer) {
            this.dialog = false;
            if (answer === "yes") {
                this.$root.trigger("pkg_destroy", this.pack);
            }
        },
    },
    computed: {
        message: function() {
            return "Please confirm delivery cancellation for pack " + this.pack.name;
        },
    },
    template: `
  <div class="action action-destroy">
    <v-dialog v-model="dialog" fullscreen tile class="actions fullscreen text-center">
      <template v-slot:activator="{ on }">
        <v-btn class="destroy" depressed small rounded color="error" v-on="on">&#10006;</v-btn>
      </template>
      <v-card>
        <user-confirmation
            v-on:user-confirmation="on_user_confirm"
            v-bind:question="message"></user-confirmation>
      </v-card>
    </v-dialog>
  </div>
`,
});

Vue.component("checkout-summary-product-detail", {
    props: {
        record: Object,
        index: Number,
        count: Number,
    },
    template: `
        <div class="summary-content-item">
            <v-list-item-title>
                <span class="item-counter">
                    <span>{{ index + 1 }} / {{ count }}</span>
                </span>
                {{ record.product.display_name }}
            </v-list-item-title>
            <v-list-item-subtitle>
                <div class="lot" v-if="record.lot">
                    <span class="label">Lot:</span> <span>{{ record.lot.name }}</span>
                </div>
                <div class="qty">
                    <span class="label">Qty:</span> <span>{{ record.qty_done }}</span>
                </div>
            </v-list-item-subtitle>
        </div>
    `,
});
