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
}

export const utils = new Utils();
