export var checkout_picking_detail = Vue.component('checkout-picking-detail', {
    props: {
        'info': Object,
        'grouped_lines': Array,
        // TODO: maybe this should be provided by manual select component
        'select_options': {
            'type': Object,
            'default': function () {
                return {};
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
        :key_value="'id'"
        :list_item_content_component="'checkout-select-content'"
        :bubbleUpAction="true"
        :showActions="false"
        :multiple="select_options.multiple"
        :initSelectAll="select_options.initSelectAll"
        />
</div>
`,
});

Vue.component('checkout-select-content', {
    props: {
        'record': Object,
        'options': Object,
    },
    template: `
    <div>
        <div class="has_pack" v-if="record.pack">
            <span>{{ record.pack.name }}</span>
        </div>
        <div class="no_pack" v-if="!record.pack">
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
