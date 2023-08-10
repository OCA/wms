/**
 * Copyright 2021 ACSONE SA/NV
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

/* eslint-disable strict */
Vue.component("pack-picking-detail", {
    props: ["record"],
    methods: {
        move_lines_color_klass(rec) {
            let line = rec;
            if (line._is_group) {
                line = line.records[0];
            }
            let klass = "";
            if (this.record.scanned_packs.includes(line.package_dest.id)) {
                klass = "done screen_step_done lighten-1";
            } else {
                klass = "not-done screen_step_todo lighten-1";
            }
            return "move-line-" + klass;
        },
        line_list_options() {
            return {
                card_klass: "loud-labels",
                key_title: "",
                showCounters: false,
                list_item_options: {
                    fields: this.line_list_fields(),
                    list_item_klass_maker: this.move_lines_color_klass,
                },
            };
        },
        line_list_fields() {
            self = this;
            return [
                {
                    path: "product.display_name",
                    action_val_path: "product.default_code",
                    klass: "loud",
                },
                {
                    path: "package_src.name",
                    label: "Pack",
                    action_val_path: "package_src.name",
                },
                {path: "lot.name", label: "Lot", action_val_path: "lot.name"},
                {
                    path: "qty_done",
                    label: "Qty",
                    render_component: "packaging-qty-picker-display",
                    render_props: function (record) {
                        return self.utils.wms.move_line_qty_picker_props(record, {
                            qtyInit: record.qty_done,
                        });
                    },
                },
            ];
        },
        grouped_lines() {
            const groups = this.utils.wms.group_by_pack(
                this.record.move_lines.filter((op) => {
                    if (op.package_dest != null && op.package_dest.is_internal) {
                        return op;
                    }
                })
            );
            const self = this;
            _.forEach(groups, function (item) {
                item.group_color = self.record.scanned_packs.includes(item.pack.id)
                    ? self.utils.colors.color_for("screen_step_done")
                    : self.utils.colors.color_for("screen_step_todo");
            });
            return groups;
        },
    },
    template: `
  <div class="review">
    <v-card class="main">
        <v-card-title>
            <div class="main-info">
                    {{ record.name }} : {{ record.partner.name }}
            </div>
        </v-card-title>
    </v-card>
    <list
        :records="record.move_lines"
        :grouped_records="grouped_lines()"
        :options="line_list_options()"
        />
  </div>

`,
});
