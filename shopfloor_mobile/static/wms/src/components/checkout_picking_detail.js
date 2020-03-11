var CheckoutPickingDetailMixin = {
    props: {
        'info': Object,
        'grouped_lines': Array,
        // TODO: maybe this should be provided by manual select component
        'select_options': {
            'type': Object,
            'default': function () {
                return {
                    'showActions': false,
                    'list_item_component': 'checkout-select-content',
                };
            },
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
        :records="info.lines"
        :grouped_records="grouped_lines"
        :options="select_options"
        />
</div>
`,
};

var checkout_picking_detail = Vue.component('checkout-picking-detail', {
    mixins: [CheckoutPickingDetailMixin],
});

Vue.component('checkout-select-content', {
    props: {
        'record': Object,
        'options': Object,
        'index': Number,
        'count': Number,
    },
    template: `
    <div>
        <div class="has_pack" v-if="record.pack">
            <div class="item-counter">
                <span>{{ index + 1 }} / {{ count }}</span>
            </div>
            <span>{{ record.pack.name }}</span>
        </div>
        <div class="no_pack" v-if="!record.pack">
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

var checkout_summary_detail = Vue.component('checkout-summary-detail', {
    mixins: [CheckoutPickingDetailMixin],
    props: {
        // TODO: maybe this should be provided by manual select component
        'select_options': {
            'type': Object,
            'default': function () {
                return {
                    multiple: true,
                    initSelectAll: true,
                    showCounters: true,
                    list_item_component: 'checkout-summary-content',
                    list_item_extra_component: 'checkout-summary-extra-content',
                };
            },
        },
    },
});


Vue.component('checkout-summary-content', {
    props: {
        'record': Object,
        'options': Object,
        'index': Number,
        'count': Number,
    },
    methods: {
        debug_it: function (record) {
            console.dir(record);
        },
    },
    template: `
    <div class="summary-content">
        <div class="has-pack" v-if="record.key != 'no-pack'">
            <v-list-item-title>
                <span class="item-counter">
                    <span>{{ index + 1 }} / {{ count }}</span>
                </span>
                {{ record.title }}
            </v-list-item-title>
        </div>
        <div class="no-pack" v-else>
            <div v-for="(subrec, i) in record.records">
                <checkout-summary-product-detail :record="subrec" />
            </div>
        </div>
    </div>
    `,
});


Vue.component('checkout-summary-product-detail', {
    props: {
        'record': Object,
    },
    template: `
        <div class="summary-content-item">
            <v-list-item-title v-text="record.product.display_name"></v-list-item-title>
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


Vue.component('checkout-summary-extra-content', {
    props: {
        'record': Object,
    },
    methods: {
        debug_it: function (record) {
            console.dir(record);
            debugger;
        },
    },
    template: `
    <div>
    <!--{{ debug_it(record) }} -->
    <v-expansion-panels flat v-if="record.key != 'no-pack' && record.records_by_pkg_type">
        <v-expansion-panel v-for="pkg_type in record.records_by_pkg_type" :key="pkg_type.key">
            <v-expansion-panel-header>
                <span>{{ pkg_type.title }}</span>
            </v-expansion-panel-header>
            <v-expansion-panel-content>
                <div v-for="(prod, i) in pkg_type.records">
                    <checkout-summary-product-detail :record="prod" />
                </div>
            </v-expansion-panel-content>
        </v-expansion-panel>
    </v-expansion-panels>
    </div>
    `,
});
