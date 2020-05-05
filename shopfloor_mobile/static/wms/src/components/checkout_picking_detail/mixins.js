/* eslint-disable strict */
/* eslint-disable no-implicit-globals */
import {PickingDetailMixin} from "../detail/detail_picking.js";

export var CheckoutPickingDetailSelectMixin = {
    mixins: [PickingDetailMixin],
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
<div class="detail-picking-select" v-if="!_.isEmpty(picking)">

    <detail-picking :picking="picking" />

    <manual-select
        :records="select_records || picking.move_lines"
        :grouped_records="select_records_grouped"
        :options="select_opts"
        />
</div>
`,
};

export var CheckoutPickingDetailListMixin = {
    mixins: [PickingDetailMixin],
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
<div class="detail-picking-list" v-if="!_.isEmpty(picking)">

    <detail-picking :picking="picking" />

    <list
        :records="records || picking.move_lines"
        :grouped_records="records_grouped"
        :options="list_opts"
        />
</div>
`,
};
