export var checkout_picking_info = Vue.component('checkout-picking-detail', {
    props: ['info'],
    methods: {
        group_lines_by_location: function (lines) {
            // {'key': 'no-group', 'title': '', 'records': []}
            const res = [];
            const locations = _.uniqBy(_.map(lines, function (x) {
                return x.location_src;
            }), 'id');
            const grouped = _.groupBy(lines, 'location_src.id');
            _.forEach(grouped, function (value, loc_id) {
                const location = _.first(_.filter(locations, {'id': parseInt(loc_id)}));
                res.push({
                    'key': loc_id,
                    'title': 'Location: ' + location.name,
                    'records': value,
                });
            });
            return res;
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
        :records="group_lines_by_location(info.lines)"
        :grouped="true"
        :key_value="'id'"
        :list_item_content_component="'checkout-select-content'"
        :bubbleUpAction="true"
        :showActions="false"
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
