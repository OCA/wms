/* eslint-disable strict */
/* eslint-disable no-implicit-globals */
import {PickingDetailMixin} from "../detail/detail_picking.js";

// Maybe worth to move it to its own file
export var ListActionsConsumerMixin = {
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
                    // more options here if needed
                }
            );
            return opts;
        },
    },
};

export var PickingDetailSelectMixin = {
    mixins: [PickingDetailMixin, ListActionsConsumerMixin],
    props: {
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
<div class="detail-picking-select" v-if="!_.isEmpty(picking)">

    <detail-picking :picking="picking" />

    <manual-select
        :records="select_records || picking.move_lines"
        :grouped_records="select_records_grouped"
        :options="select_opts()"
        />
</div>
`,
};

export var PickingDetailListMixin = {
    mixins: [PickingDetailMixin, ListActionsConsumerMixin],
    props: {
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
<div class="detail-picking-list" v-if="!_.isEmpty(picking)">

    <detail-picking :picking="picking" />

    <list
        :records="records || picking.move_lines"
        :grouped_records="records_grouped"
        :options="list_opts()"
        />
</div>
`,
};
