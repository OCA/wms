/* eslint-disable strict */
/* eslint-disable no-implicit-globals */
export var CheckoutPickingDetailMixin = {
    props: {
        picking: Object,
    },
    template: `
<div class="detail checkout-picking-detail" v-if="!_.isEmpty(picking)">
    <v-card outlined class="main">
        <v-card-title>{{ picking.name }}</v-card-title>
        <v-card-subtitle>
            <span class="origin" v-if="picking.origin">
                <span>{{ picking.origin }}</span>
            </span>
            <span v-if="picking.origin && picking.partner"> - </span>
            <span class="partner" v-if="picking.partner">
                <span>{{ picking.partner.name }}</span>
            </span>
        </v-card-subtitle>
    </v-card>
</div>
`,
};

export var CheckoutPickingDetailSelectMixin = {
    mixins: [CheckoutPickingDetailMixin],
    props: {
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
<div class="checkout-picking-detail-select" v-if="!_.isEmpty(picking)">

    <checkout-picking-detail :picking="picking" />

    <manual-select
        :records="select_records || picking.move_lines"
        :grouped_records="select_records_grouped"
        :options="select_opts"
        />
</div>
`,
};

export var CheckoutPickingDetailListMixin = {
    mixins: [CheckoutPickingDetailMixin],
    props: {
        records: Array,
        records_grouped: Array,
        list_options: Object,
    },
    computed: {
        list_opts() {
            // Defining defaults for an Object property
            // works only if you don't pass the property at all.
            // If you pass only one key, you'll lose all defaults.
            const opts = _.defaults({}, this.$props.list_options, {
                showCounters: false,
            });
            return opts;
        },
    },
    template: `
<div class="checkout-picking-detail-list" v-if="!_.isEmpty(picking)">

    <checkout-picking-detail :picking="picking" />

    <list
        :records="records || picking.move_lines"
        :grouped_records="records_grouped"
        :options="list_opts"
        />
</div>
`,
};

