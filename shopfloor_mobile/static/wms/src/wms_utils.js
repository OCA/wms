/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */
import {utils_registry} from "/shopfloor_mobile_base/static/wms/src/services/utils_registry.js";

export class WMSUtils {
    group_lines_by_location(lines, options) {
        const self = this;
        // {'key': 'no-group', 'title': '', 'records': []}
        options = _.defaults(options || {}, {
            group_key: "location_src",
            group_no_title: false,
            name_prefix: "Location",
            prepare_records: function (recs) {
                return recs;
            },
            group_color_maker: function (recs) {
                return "";
            },
        });
        const res = [];
        const locations = _.uniqBy(
            _.map(lines, function (x) {
                return x[options.group_key];
            }),
            "id"
        );
        const grouped = _.groupBy(lines, options.group_key + ".id");
        // TODO: grouped.forEach?
        _.forEach(grouped, function (value, loc_id) {
            const location = _.first(_.filter(locations, {id: parseInt(loc_id, 10)}));
            const title = options.group_no_title
                ? ""
                : options.name_prefix
                ? options.name_prefix + ": " + location.name
                : location.name;
            res.push({
                _is_group: true,
                key: loc_id,
                title: title,
                group_color: options.group_color_maker(value),
                records: options.prepare_records.call(self, value),
            });
        });
        return res;
    }

    group_lines_by_locations(lines, options) {
        const self = this;
        // {key: 'no-group', location_src: {}, location_dest: {} records: []}
        options = _.defaults(options || {}, {
            prepare_records: function (recs) {
                return recs;
            },
        });
        const res = [];
        const locations = _.uniqBy(
            _.concat(
                _.map(lines, function (x) {
                    return x.location_src;
                }),
                _.map(lines, function (x) {
                    return x.location_dest;
                })
            ),
            "id"
        );
        const grouped = _.chain(lines)
            .groupBy((item) => `${item.location_src.id}--${item.location_dest.id}`)
            .value();
        _.forEach(grouped, function (value, loc_ids) {
            const [src_id, dest_id] = loc_ids.split("--");
            const src_loc = _.first(_.filter(locations, {id: parseInt(src_id, 10)}));
            const dest_loc = _.first(_.filter(locations, {id: parseInt(dest_id, 10)}));
            res.push({
                _is_group: true,
                key: loc_ids,
                location_src: src_loc,
                location_dest: dest_loc,
                records: options.prepare_records.call(self, value),
            });
        });
        return res;
    }

    group_lines_by_product(lines, options) {
        const self = this;
        // {'key': 'no-group', 'title': '', 'records': []}
        options = _.defaults(options || {}, {
            group_no_title: false,
            prepare_records: function (recs) {
                return recs;
            },
            group_color_maker: function (recs) {
                return "";
            },
        });
        const res = [];
        const products = _.uniqBy(
            _.map(lines, function (x) {
                return x["product"];
            }),
            "id"
        );
        const grouped = _.groupBy(lines, "product.id");
        _.forEach(grouped, function (value, prod_id) {
            const product = _.first(_.filter(products, {id: parseInt(prod_id, 10)}));
            const title = options.group_no_title
                ? ""
                : options.name_prefix
                ? options.name_prefix + ": " + product.name
                : product.name;
            res.push({
                _is_group: true,
                key: prod_id,
                title: title,
                group_color: options.group_color_maker(value),
                records: options.prepare_records.call(self, value),
            });
        });
        return res;
    }

    group_by_pack(lines, package_key = "package_dest") {
        const self = this;
        const res = [];
        const packs = _.uniqBy(
            _.map(lines, function (x) {
                return _.result(x, package_key);
            }),
            "id"
        );
        const grouped = _.groupBy(lines, function (l) {
            const pack_id = _.result(l, package_key + ".id");
            if (pack_id) {
                return "pack-" + pack_id;
            }
            return "raw-" + l.id + l.product.id;
        });
        let counter = 0;
        _.forEach(grouped, function (products, key) {
            counter++;
            let pack = null;
            if (key.startsWith("pack")) {
                pack = _.first(
                    _.filter(packs, {id: parseInt(key.split("-").slice(-1)[0], 10)})
                );
            }
            res.push({
                _is_group: true,
                key: key + "--" + counter,
                // No pack, just display the product name
                title: pack ? pack.name : products[0].display_name,
                pack: pack,
                records: products,
                records_by_pkg_type: pack ? self.group_by_package_type(products) : null,
            });
        });
        return res;
    }

    group_by_package_type(lines) {
        const res = [];
        const grouped = _.groupBy(lines, "package_dest.packaging.name");
        _.forEach(grouped, function (products, packaging_name) {
            res.push({
                _is_group: true,
                // GroupBy gives undefined as string
                key: packaging_name == "undefined" ? "no-packaging" : packaging_name,
                title: packaging_name == "undefined" ? "" : packaging_name,
                records: products,
            });
        });
        return res;
    }

    only_one_package(lines) {
        const res = [];
        const pkg_seen = [];
        lines.forEach(function (line) {
            if (line.package_dest) {
                if (!pkg_seen.includes(line.package_dest.id)) {
                    // Got a pack
                    res.push(line);
                    pkg_seen.push(line.package_dest.id);
                }
            } else {
                // No pack
                res.push(line);
            }
        });
        return res;
    }

    completed_move_lines(move_lines) {
        return _.filter(move_lines, function (l) {
            return l.qty_done > 0;
        }).length;
    }

    move_lines_completeness(move_lines) {
        return (this.completed_move_lines(move_lines) / move_lines.length) * 100;
    }

    picking_completeness(record, filtered_move_lines) {
        const move_lines = filtered_move_lines
            ? filtered_move_lines
            : record.move_lines;
        return this.move_lines_completeness(move_lines);
    }

    order_picking_by_completeness(pickings) {
        const self = this;
        const ordered = _.sortBy(pickings, function (rec) {
            return self.picking_completeness(rec);
        });
        return _.reverse(ordered);
    }

    move_line_color_klass(rec) {
        let line = rec;
        if (line._is_group) {
            line = line.records[0];
        }
        let klass = "";
        if (line.qty_done == line.quantity) {
            klass = "done screen_step_done lighten-1";
        } else if (line.qty_done && line.qty_done < line.quantity) {
            klass = "partial screen_step_todo lighten-2";
        } else if (line.qty_done == 0) {
            klass = "not-done screen_step_todo lighten-1";
        }
        return "move-line-" + klass;
    }

    list_item_klass_maker_by_progress(rec) {
        const records = _.result(rec, "records", undefined);
        if (!records) {
            return;
        }
        let avg_progress =
            records.reduce((acc, next) => {
                return next.progress + acc;
            }, 0) / records.length;
        let klass = "";
        if (avg_progress === 100) {
            klass = "done screen_step_done lighten-1";
        } else if (avg_progress === 0) {
            klass = "not-done screen_step_todo lighten-1";
        } else {
            klass = "partial screen_step_todo lighten-2";
        }
        return "move-line-" + klass;
    }

    /**
     * Provide display options for rendering move line product's info.
     *
     * TODO: @simahawk this is a first attempt to stop creating a specific widget of each case
     * whereas you have to handle different options.
     * The aim is to be able to re-use detail-card and alike by passing options only.
     *
     * @param {*} line The move line
     */
    move_line_product_detail_options(line, options = {}) {
        const self = this;
        const default_fields = [
            {path: "product.supplier_code", label: "Vendor code", klass: "loud"},
            {path: "package_src.name", label: "Pack"},
            {path: "lot.name", label: "Lot"},
            {
                path: "quantity",
                label: "Qty",
                render_component: "packaging-qty-picker-display",
                render_props: function (record) {
                    return self.move_line_qty_picker_props(record, {
                        qtyInit: record.quantity,
                    });
                },
            },
            {path: "product.qty_available", label: "Qty on hand"},
        ];
        options = _.defaults({}, options, {
            main: true,
            key_title: "product.display_name",
            title_action_field: {action_val_path: "product.barcode"},
            fields_blacklist: [],
            fields_extend_default: true,
        });
        options.fields = options.fields_extend_default
            ? default_fields.concat(options.fields || [])
            : options.fields || [];
        options.fields = _.filter(options.fields, function (field) {
            return !options.fields_blacklist.includes(field.path);
        });
        return options;
    }
    move_line_qty_picker_options(line, override = {}) {
        // DEPRECATED - To drop in next versions
        // Use v-bind="utils.wms.move_line_qty_picker_props(...)" instead
        console.log("wms_utils.move_line_qty_picker_options is deprecated.");
    }
    move_line_qty_picker_props(line, override = {}) {
        const props = {
            qtyTodo: parseInt(line.quantity, 10),
            qtyInit: line.qty_done,
            availablePackaging: line.product.packaging,
            uom: line.product.uom,
            nonZeroOnly: true,
        };
        return _.extend(props, override || {});
    }
}

utils_registry.add("wms", new WMSUtils());
