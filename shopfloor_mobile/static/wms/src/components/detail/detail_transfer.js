import {ItemDetailMixin} from "./detail_mixin.js";

Vue.component("detail-transfer", {
    mixins: [ItemDetailMixin],
    methods: {
        detail_fields() {
            const self = this;
            return [
                {
                    path: "scheduled_date",
                    label: "Scheduled on",
                    klass: "loud-label",
                    renderer: function(rec, field) {
                        return self.utils.misc.render_field_date(rec, field);
                    },
                },
                {
                    path: "operation_type.name",
                    label: "Operation type",
                },
                {path: "carrier.name", label: "Carrier"},
                {path: "priority", label: "Priority"},
                {path: "note"},
            ];
        },
        picking_detail_options() {
            return _.defaults({}, this.opts, {
                main: true,
            });
        },
        line_list_fields() {
            return [
                {
                    path: "product.display_name",
                    action_val_path: "product.barcode",
                    klass: "loud",
                },
                {
                    path: "package_src.name",
                    label: "Pack",
                    action_val_path: "package_src.name",
                },
                {path: "lot.name", label: "Lot", action_val_path: "lot.name"},
                {path: "product.qty_reserved", label: "Qty reserved"},
                {path: "product.qty_available", label: "Qty in stock"},
            ];
        },
        grouped_lines() {
            return this.utils.misc.group_lines_by_locations(this.record.move_lines);
        },
    },
    template: `
    <div :class="$options._componentTag">
        <detail-picking
            :key="record.id"
            :record="record"
            :options="picking_detail_options()"
            />

        <div class="lines" v-if="(record.move_lines || []).length">
            <div v-for="group in grouped_lines()">
                <separator-title>
                    {{group.location_src.name}} -> {{ group.location_dest.name }}
                </separator-title>
                <list
                    :records="group.records"
                    :key="'group-' + group.key"
                    :options="{key_title: '', list_item_options: {fields: line_list_fields(), list_item_klass_maker: utils.misc.move_line_color_klass}}"
                    />
            </div>
        </div>
    </div>
`,
});
