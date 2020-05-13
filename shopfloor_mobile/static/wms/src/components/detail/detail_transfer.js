import {ItemDetailMixin} from "./detail_mixin.js";
import {utils} from "../../utils.js";

Vue.component("detail-transfer", {
    mixins: [ItemDetailMixin],
    methods: {
        detail_fields() {
            return [
                {
                    path: "scheduled_date",
                    label: "Scheduled on",
                    klass: "loud-label",
                    renderer: this._render_date,
                },
                {
                    path: "operation_type.name",
                },
                {path: "carrier.name"},
                {path: "priority"},
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
                {path: "product.display_name", klass: "loud"},
                {path: "package_src.name", label: "Pack"},
                {path: "lot.name", label: "Lot"},
                {path: "product.qty_reserved", label: "Qty reserved"},
                {path: "product.qty_available", label: "Qty in stock"},
            ];
        },
        grouped_lines() {
            return utils.group_lines_by_locations(this.record.lines);
        },
        line_list_color_klass(line) {
            let klass = "";
            if (line.qty_done == line.quantity) {
                klass = "done";
            } else if (line.qty_done && line.qty_done < line.quantity) {
                klass = "partial";
            } else if (line.qty_done == 0) {
                klass = "not-done";
            }
            return "transfer-line-" + klass;
        },
    },
    template: `
    <div :class="$options._componentTag">
        <detail-picking
            :key="record.id"
            :picking="record"
            :options="picking_detail_options()"
            />

        <div class="lines" v-if="record.lines.length">
            <div v-for="group in grouped_lines()">
                <separator-title>
                    {{group.location_src.name}} -> {{ group.location_dest.name }}
                </separator-title>
                <list
                    :records="group.records"
                    :key="'group-' + group.key"
                    :options="{key_title: '', list_item_options: {fields: line_list_fields(), list_item_klass_maker: line_list_color_klass}}"
                    />
            </div>
        </div>
    </div>
`,
});
