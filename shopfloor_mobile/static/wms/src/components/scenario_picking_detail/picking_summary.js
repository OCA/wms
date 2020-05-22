/* eslint-disable strict */
/* eslint-disable no-implicit-globals */
import {PickingDetailListMixin} from "./mixins.js";

Vue.component("picking-summary", {
    mixins: [PickingDetailListMixin],
    methods: {
        list_opts() {
            const opts = _.defaults(
                {},
                this.$super(PickingDetailListMixin).list_opts(),
                {
                    showCounters: true,
                    list_item_component: "picking-summary-content",
                }
            );
            return opts;
        },
        _get_available_list_item_actions() {
            // TODO: we should probably make the 1st class citizens w/ their own object class.
            return {
                action_change_pkg: {
                    comp_name: "edit-action",
                    get_record: function(rec, action) {
                        if (rec.pack) {
                            // lines grouped, get real line
                            return rec.pack;
                        }
                        return rec.package_dest;
                    },
                    options: {
                        click_event: "pkg_change_type",
                    },
                    enabled: function(rec, action) {
                        // Exclude for non-packaged records.
                        // NOTE: `pack` is available only if records are grouped.
                        // See `utils.group_by_pack`.
                        return !_.isUndefined(rec.pack);
                    },
                },
                action_cancel_line: {
                    comp_name: "cancel-move-line-action",
                    options: {},
                    get_record: function(rec, action) {
                        if (rec.records) {
                            // lines grouped, get real line
                            return rec.records[0];
                        }
                        return rec;
                    },
                    enabled: function(rec, action) {
                        return true;
                    },
                },
            };
        },
    },
});

Vue.component("picking-summary-content", {
    props: {
        record: Object,
        options: Object,
        index: Number,
        count: Number,
    },
    data: function() {
        return {
            panel: [],
        };
    },
    watch: {
        panel: {
            handler: function(newVal, oldVal) {
                // The panel is opened
                $(this.$parent.$el).toggleClass("inner-panel-expanded", newVal == 0);
            },
        },
    },
    template: `
    <v-list-item-content :class="'summary-content ' + (record.key == 'no-pack'? 'no-pack' : 'has-pack' )">
        <v-expansion-panels v-if="record.key != 'no-pack' && record.records_by_pkg_type" flat v-model="panel">
            <v-expansion-panel v-for="pkg_type in record.records_by_pkg_type" :key="make_component_key(['pkg', index])">
                <v-expansion-panel-header>
                    <span class="item-counter">
                        <span>{{ index + 1 }} / {{ count }}</span>
                    </span>
                    {{ record.title }}
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                    <strong class="pkg-type-name">{{ pkg_type.title }}</strong>
                    <picking-summary-product-detail
                        v-for="(prod, i) in pkg_type.records"
                        :record="prod"
                        :index="i"
                        :count="pkg_type.records.length"
                        />
                </v-expansion-panel-content>
            </v-expansion-panel>
        </v-expansion-panels>
        <div v-else v-for="(subrec, i) in record.records">
            <picking-summary-product-detail :record="subrec" :index="index" :count="count" :key="make_component_key(['bare', subrec.id])" />
        </div>
    </v-list-item-content>
    `,
});

Vue.component("picking-summary-product-detail", {
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
