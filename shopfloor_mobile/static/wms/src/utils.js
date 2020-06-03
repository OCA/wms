export class Utils {
    constructor() {}

    group_lines_by_location(lines, options) {
        let self = this;
        // {'key': 'no-group', 'title': '', 'records': []}
        options = _.defaults(options || {}, {
            group_key: "location_src",
            name_prefix: "Location",
            prepare_records: function(recs) {
                return recs;
            },
            group_color_maker: function(recs) {
                return "";
            },
        });
        const res = [];
        const locations = _.uniqBy(
            _.map(lines, function(x) {
                return x[options.group_key];
            }),
            "id"
        );
        const grouped = _.groupBy(lines, options.group_key + ".id");
        _.forEach(grouped, function(value, loc_id) {
            const location = _.first(_.filter(locations, {id: parseInt(loc_id)}));
            const title = options.name_prefix
                ? options.name_prefix + ": " + location.name
                : location.name;
            res.push({
                key: loc_id,
                title: title,
                group_color: options.group_color_maker(value),
                records: options.prepare_records.call(self, value),
            });
        });
        return res;
    }

    group_lines_by_locations(lines, options) {
        let self = this;
        // {key: 'no-group', location_src: {}, location_dest: {} records: []}
        options = _.defaults(options || {}, {
            prepare_records: function(recs) {
                return recs;
            },
        });
        const res = [];
        const locations = _.uniqBy(
            _.concat(
                _.map(lines, function(x) {
                    return x.location_src;
                }),
                _.map(lines, function(x) {
                    return x.location_dest;
                })
            ),
            "id"
        );
        const grouped = _.chain(lines)
            .groupBy(item => `${item.location_src.id}--${item.location_dest.id}`)
            .value();
        _.forEach(grouped, function(value, loc_ids) {
            const [src_id, dest_id] = loc_ids.split("--");
            const src_loc = _.first(_.filter(locations, {id: parseInt(src_id)}));
            const dest_loc = _.first(_.filter(locations, {id: parseInt(dest_id)}));
            res.push({
                key: loc_ids,
                location_src: src_loc,
                location_dest: dest_loc,
                records: options.prepare_records.call(self, value),
            });
        });
        return res;
    }

    group_by_pack(lines) {
        let self = this;
        const res = [];
        const packs = _.uniqBy(
            _.map(lines, function(x) {
                return x.package_dest;
            }),
            "id"
        );
        const grouped = _.groupBy(lines, function(l) {
            const pack_id = _.result(l, "package_dest.id");
            if (pack_id) {
                return "pack-" + pack_id;
            }
            return "raw-" + l.id + l.product.id;
        });
        let counter = 0;
        _.forEach(grouped, function(products, key) {
            counter++;
            let pack = null;
            if (key.startsWith("pack")) {
                pack = _.first(
                    _.filter(packs, {id: parseInt(key.split("-").slice(-1)[0])})
                );
            }
            res.push({
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
        _.forEach(grouped, function(products, packaging_name) {
            res.push({
                // groupBy gives undefined as string
                key: packaging_name == "undefined" ? "no-packaging" : packaging_name,
                title: packaging_name == "undefined" ? "" : packaging_name,
                records: products,
            });
        });
        return res;
    }

    only_one_package(lines) {
        let res = [];
        let pkg_seen = [];
        lines.forEach(function(line) {
            if (line.package_dest) {
                if (!pkg_seen.includes(line.package_dest.id)) {
                    // got a pack
                    res.push(line);
                    pkg_seen.push(line.package_dest.id);
                }
            } else {
                // no pack
                res.push(line);
            }
        });
        return res;
    }

    picking_completed_lines(record) {
        return _.filter(record.move_lines, function(l) {
            return l.qty_done > 0;
        }).length;
    }

    picking_completeness(record) {
        return (this.picking_completed_lines(record) / record.move_lines.length) * 100;
    }

    order_picking_by_completeness(pickings) {
        const self = this;
        const ordered = _.sortBy(pickings, function(rec) {
            return self.picking_completeness(rec);
        });
        return _.reverse(ordered);
    }

    // DIsplay utils: TODO: split them to their own place

    format_date_display(date_string, options = {}) {
        _.defaults(options, {
            locale: navigator ? navigator.language : "en-US",
            format: {
                day: "numeric",
                month: "short",
                year: "numeric",
                hour: "numeric",
                minute: "2-digit",
            },
        });
        return new Date(Date.parse(date_string)).toLocaleString(
            options.locale,
            options.format
        );
    }

    move_line_color_klass(line) {
        let klass = "";
        if (line.qty_done == line.quantity) {
            klass = "done";
        } else if (line.qty_done && line.qty_done < line.quantity) {
            klass = "partial";
        } else if (line.qty_done == 0) {
            klass = "not-done";
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
    move_line_product_detail_options(line, override = {}) {
        const self = this;
        const fields = [
            {path: "package_src.name", label: "Pack"},
            {path: "lot.name", label: "Lot"},
            {
                path: "quantity",
                label: "Qty",
                render_component: "packaging-qty-picker-display",
                render_options: function(record) {
                    return self.move_line_qty_picker_options(record);
                },
            },
            {path: "product.qty_available", label: "Qty on hand"},
        ];
        let opts = {
            main: true,
            key_title: "product.display_name",
            fields: fields,
            title_action_field: {action_val_path: "product.barcode"},
        };
        return _.extend(opts, override || {});
    }
    move_line_qty_picker_options(line, override = {}) {
        let opts = {
            init_value: line.quantity,
            available_packaging: line.product.packaging,
            uom: line.product.uom,
        };
        return _.extend(opts, override || {});
    }
}

export const utils = new Utils();
