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
            // TODO: we should call `super.list_options` but is not available in vue by default.
            const opts = _.defaults({}, this.$props.list_options, {
                showCounters: true,
                list_item_component: "checkout-summary-content",
                list_item_actions: this._get_list_item_actions(
                    this.$props.list_options.list_item_options.actions || []
                ),
            });
            // _.defaults is not recursive
            opts.list_item_options = _.defaults(
                {},
                this.$props.list_options.list_item_options,
                {
                    // more options here
                }
            );
            return opts;
        },
    },
    methods: {
        _get_list_item_actions(to_enable) {
            let actions = [];
            const avail_list_item_actions = this._get_available_list_item_actions();
            to_enable.forEach(function(action) {
                if (
                    typeof action === "string" &&
                    !_.isUndefined(avail_list_item_actions[action])
                ) {
                    actions.push(avail_list_item_actions[action]);
                } else {
                    // we might get an action description object straight
                    actions.push(action);
                }
            });
            return actions;
        },
        _get_available_list_item_actions() {
            // TODO: we should probably make the 1st class citizens w/ their own object class.
            return {
                action_change_pkg: {
                    comp_name: "edit-action",
                    get_record: function(rec, action) {
                        if (rec.records) {
                            // lines grouped, get real line
                            return rec.records[0].package_src;
                        }
                        return rec.package_src;
                    },
                    options: {
                        click_event: "pkg_change_type",
                    },
                    enabled: function(rec, action) {
                        // Exclude for non-packaged records.
                        // NOTE: `pack` is available only if records are grouped.
                        // See `utils.group_by_pack`.
                        return Boolean(rec.pack);
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

Vue.component("checkout-summary-content", {
    props: {
        record: Object,
        options: Object,
        index: Number,
        count: Number,
    },
    template: `
    <v-list-item-content :class="'summary-content ' + (record.key == 'no-pack'? 'no-pack' : 'has-pack' )">
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
                    <!--edit-action :record="record.pack" :click_event="'pkg_change_type'" /-->
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
