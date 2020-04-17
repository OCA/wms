/* eslint-disable strict */
/* eslint-disable no-implicit-globals */
var CheckoutPickingDetailMixin = {
    props: {
        info: Object,
        select_records: Array,
        select_records_grouped: Array,
        select_options: Object,
    },
    computed: {
        select_opts() {
            // Defining defaults for an Object property
            // works only if you don't pass the property at all.
            // If you pass only one key, you'll lose all defaults.
            const opts = _.defaults({}, this.$props.select_options, {
                showActions: false,
                list_item_component: "checkout-select-line-content",
            });
            return opts;
        },
    },
    template: `
<div class="detail checkout-picking-detail" v-if="!_.isEmpty(info)">
    <v-card outlined class="main">
        <v-card-title>{{ info.name }}</v-card-title>
        <v-card-subtitle>
            <span class="origin" v-if="info.origin">
                <span>{{ info.origin }}</span>
            </span>
            <span v-if="info.origin && info.partner"> - </span>
            <span class="partner" v-if="info.partner">
                <span>{{ info.partner.name }}</span>
            </span>
        </v-card-subtitle>
    </v-card>

    <manual-select
        :records="select_records || info.move_lines"
        :grouped_records="select_records_grouped"
        :options="select_opts"
        />
</div>
`,
};

Vue.component("checkout-picking-detail", {
    mixins: [CheckoutPickingDetailMixin],
});

Vue.component("checkout-select-line-content", {
    props: {
        record: Object,
        options: Object,
        index: Number,
        count: Number,
    },
    template: `
    <div>
        <div class="has_pack" v-if="record.package_dest">
            <div class="item-counter">
                <span>{{ index + 1 }} / {{ count }}</span>
            </div>
            <span>{{ record.package_dest.name }}</span>
        </div>
        <div class="no_pack" v-if="!record.package_dest">
            <div class="item-counter">
                <span>{{ index + 1 }} / {{ count }}</span>
            </div>
            <span>{{ record.product.display_name }}</span>
            <div class="lot" v-if="record.lot">
                <span class="label">Lot:</span> <span>{{ record.lot.name }}</span>
            </div>
            <div class="qty">
                <span class="label">Qty:</span> <span>{{ record.product.qty }}</span>
            </div>
        </div>
    </div>
  `,
});

Vue.component("checkout-select-package-content", {
    props: {
        record: Object,
        options: Object,
        index: Number,
        count: Number,
    },
    template: `
    <div>
        <div :class="record.package_dest ? 'has-pack' : 'no-pack'">
            <span>{{ record.product.display_name }}</span>
            <div class="lot" v-if="record.lot">
                <span class="label">Lot:</span> <span>{{ record.lot.name }}</span>
            </div>
            <div class="qty">
                <span class="label">Qty:</span> <span>{{ record.qty_done }} / {{ record.quantity }}</span>
            </div>
        </div>
    </div>
  `,
});

Vue.component("checkout-summary-detail", {
    mixins: [CheckoutPickingDetailMixin],
    computed: {
        select_opts() {
            // Defining defaults for an Object property
            // works only if you don't pass the property at all.
            // If you pass only one key, you'll lose all defaults.
            const opts = _.defaults({}, this.$props.select_options, {
                multiple: true,
                initSelectAll: true,
                showCounters: true,
                list_item_component: "checkout-summary-content",
                list_item_extra_component: "checkout-summary-extra-content",
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
    <div class="summary-content">
        <div class="has-pack" v-if="record.key != 'no-pack'">
            <checkout-summary-destroy-action :pack="record.pack" />
            <v-list-item-title>
                <span class="item-counter">
                    <span>{{ index + 1 }} / {{ count }}</span>
                </span>
                {{ record.title }}
            </v-list-item-title>
        </div>
        <div class="no-pack" v-else>
            <div v-for="(subrec, i) in record.records">
                <checkout-summary-product-detail :record="subrec" :index="index" :count="count" />
            </div>
        </div>
    </div>
    `,
});

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
            return "Please confirm delivery cancellation for pack " + this.pack.name
        }
    },
    template: `
  <div class="destroy-action">
    <v-dialog v-model="dialog" fullscreen tile class="actions fullscreen text-center">
      <template v-slot:activator="{ on }">
        <v-btn class="destroy float-right" depressed small rounded color="error" v-on="on">&#10006;</v-btn>
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
                    <span class="label">Qty:</span> <span>{{ record.product.qty }}</span>
                </div>
            </v-list-item-subtitle>
        </div>
    `,
});

Vue.component("checkout-summary-extra-content", {
    props: {
        record: Object,
    },
    template: `
    <v-expansion-panels flat v-if="record.key != 'no-pack' && record.records_by_pkg_type">
        <v-expansion-panel v-for="pkg_type in record.records_by_pkg_type" :key="pkg_type.key">
            <v-expansion-panel-header>
                <span>{{ pkg_type.title }}</span>
            </v-expansion-panel-header>
            <v-expansion-panel-content>
                <div v-for="(prod, i) in pkg_type.records">
                    <checkout-summary-product-detail :record="prod" :index="i" :count="pkg_type.records.length" />
                </div>
            </v-expansion-panel-content>
        </v-expansion-panel>
    </v-expansion-panels>
    `,
});
