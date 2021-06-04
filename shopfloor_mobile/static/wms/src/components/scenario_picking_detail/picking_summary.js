/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

/* eslint-disable strict */
/* eslint-disable no-implicit-globals */
import {PickingDetailListMixin} from "./mixins.js";

Vue.component("picking-summary", {
    mixins: [PickingDetailListMixin],
    props: {
        // Take control of which package key (source or destination) is used
        // to cancel the line when cancel line action is available.
        action_cancel_package_key: {
            type: String,
            default: "package_dest",
        },
    },
    methods: {
        list_opts() {
            const opts = _.defaults(
                {},
                this.$super(PickingDetailListMixin).list_opts(),
                {
                    showCounters: true,
                    list_item_component: "picking-summary-content",
                    group_color: this.utils.colors.color_for("screen_step_done"),
                }
            );
            return opts;
        },
        _get_available_list_item_actions() {
            // TODO: we should probably make the 1st class citizens w/ their own object class.
            const self = this;
            return {
                action_change_pkg: {
                    comp_name: "edit-action",
                    get_record: function(rec, action) {
                        /**
                         * Here we can get records grouped.
                         * If lines have a dest package or not
                         * we don't care for a simple reason:
                         * if the pack is there then all grouped lines
                         * have the same package.
                         * The edit action will check by itself
                         * if the pkg is there or not and pick the right record.
                         * Hence -> always return the move line.
                         */
                        if (rec.records) {
                            return rec.records[0];
                        }
                        return rec;
                    },
                    get_options: function(rec, action) {
                        return {click_event: "pkg_change_type"};
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
                    get_options: function(rec, action) {
                        return {
                            package_cancel_key: self.$props.action_cancel_package_key,
                        };
                    },
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
    <div :class="['summary-content', record.key.startsWith('raw') ? 'no-pack' : 'has-pack']">
        <v-expansion-panels v-if="record.key != 'no-pack' && record.records_by_pkg_type" flat v-model="panel">
            <v-expansion-panel v-for="pkg_type in record.records_by_pkg_type" :key="make_component_key(['pkg', index])">
                <v-expansion-panel-header>
                    <span class="item-counter">
                        <span>{{ index + 1 }} / {{ count }}</span>
                    </span>
                    {{ record.title }}
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                    <strong class="pkg-type-name mb-2">{{ pkg_type.title }}</strong>
                    <picking-summary-product-detail
                        v-for="(prod, i) in pkg_type.records"
                        :record="prod"
                        :index="i"
                        :key="make_component_key(['pkg', index, i, prod.id])"
                        :count="pkg_type.records.length"
                        />
                </v-expansion-panel-content>
            </v-expansion-panel>
        </v-expansion-panels>
        <div v-else v-for="(subrec, i) in record.records">
            <picking-summary-product-detail :record="subrec" :index="index" :count="count" :key="make_component_key(['raw', index, subrec.id, i])" />
        </div>
    </div>
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
                    <span class="label">Qty:</span>
                    <packaging-qty-picker-display
                        :key="make_component_key(['picking-summary', 'qty-picker-widget', 'done', record.id])"
                        :options="utils.wms.move_line_qty_picker_options(record, {init_value: record.qty_done})"
                        />
                </div>
            </v-list-item-subtitle>
        </div>
    `,
});
