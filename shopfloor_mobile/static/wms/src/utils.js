export class Utils {
    constructor() {}

    group_lines_by_location(lines, options) {
        // {'key': 'no-group', 'title': '', 'records': []}
        options = _.defaults(options || {}, {
            group_key: "location_src",
            name_prefix: "Location",
            prepare_records: function(recs) {
                return recs;
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
                records: options.prepare_records(value),
            });
        });
        return res;
    }

    group_lines_by_locations(lines, options) {
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
                records: options.prepare_records(value),
            });
        });
        return res;
    }

    group_by_pack(lines) {
        const self = this;
        const res = [];
        const packs = _.uniqBy(
            _.map(lines, function(x) {
                return x.package_dest;
            }),
            "id"
        );
        const grouped = _.groupBy(lines, "package_dest.id");
        let counter = 0;
        _.forEach(grouped, function(products, pack_id) {
            counter++;
            const pack = _.first(_.filter(packs, {id: parseInt(pack_id)}));
            res.push({
                key: pack ? pack_id : products[0].id + "-" + counter,
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
        const grouped = _.groupBy(lines, "package_dest.packaging_name");
        _.forEach(grouped, function(products, packaging_name) {
            res.push({
                key: packaging_name,
                title: packaging_name,
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
}

export const utils = new Utils();
