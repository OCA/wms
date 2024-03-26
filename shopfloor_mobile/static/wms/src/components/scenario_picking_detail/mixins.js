/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */
/* eslint-disable strict */
/* eslint-disable no-implicit-globals */
import {PickingDetailMixin} from "../detail/detail_picking.js";

// Maybe worth to move it to its own file
export var ListActionsConsumerMixin = {
    methods: {
        _get_list_item_actions(to_enable) {
            const actions = [];
            const avail_list_item_actions = this._get_available_list_item_actions();
            to_enable.forEach(function (action) {
                if (
                    typeof action === "string" &&
                    !_.isUndefined(avail_list_item_actions[action])
                ) {
                    actions.push(avail_list_item_actions[action]);
                } else {
                    // We might get an action description object straight
                    actions.push(action);
                }
            });
            return actions;
        },
        _get_available_list_item_actions() {
            return [];
        },
        _get_list_options(opt_key_path) {
            const opts = _.defaults({}, _.result(this.$props, opt_key_path, {}), {
                list_item_actions: this._get_list_item_actions(
                    _.result(
                        this.$props,
                        opt_key_path + ".list_item_options.actions",
                        []
                    )
                ),
            });
            // _.defaults is not recursive
            opts.list_item_options = _.defaults(
                {},
                _.result(this.$props, opt_key_path + ".list_item_options", {}),
                {
                    // More options here if needed
                }
            );
            return opts;
        },
    },
};

export var PickingDetailSelectMixin = {
    mixins: [PickingDetailMixin, ListActionsConsumerMixin],
    props: {
        /**
         * TODO: this flag seems not to be used anymore, shall we get rid of it?
         * And since the value is always false, probably we don't need the picking at all.
         * We can always use detail-picking explicitily.
         * As a consequence, maybe, "picking" should be remove from the name
         * and we should have something like `MoveLineDetailSelect|List`
         * (which is what we need for zone picking for instance).
         *
         * */

        show_picking_info: {
            type: Boolean,
            default: false,
        },
        select_records: Array,
        select_records_grouped: Array,
        select_options: Object,
    },
    methods: {
        select_opts() {
            const opts = _.defaults({}, this._get_list_options("select_options"), {
                showActions: false,
                list_item_component: "picking-select-line-content",
            });
            return opts;
        },
    },
    template: `
<div class="detail-picking-select" v-if="!_.isEmpty(record)">

    <detail-picking :record="record" v-if="show_picking_info" />

    <manual-select
        :records="select_records || record.move_lines"
        :grouped_records="select_records_grouped"
        :options="select_opts()"
        />
</div>
`,
};

export var PickingDetailListMixin = {
    mixins: [PickingDetailMixin, ListActionsConsumerMixin],
    props: {
        show_picking_info: {
            type: Boolean,
            default: false,
        },
        records: Array,
        records_grouped: Array,
        list_options: Object,
    },
    methods: {
        list_opts() {
            const opts = _.defaults({}, this._get_list_options("list_options"), {
                showCounters: false,
            });
            return opts;
        },
    },
    template: `
<div class="detail-picking-list" v-if="!_.isEmpty(record)">

    <detail-picking :record="record" v-if="show_picking_info" />

    <list
        :records="records || record.move_lines"
        :grouped_records="records_grouped"
        :options="list_opts()"
        />
</div>
`,
};
