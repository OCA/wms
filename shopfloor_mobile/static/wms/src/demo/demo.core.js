export class DemoTools {

    constructor (demo_cases) {
        this.demo_cases = demo_cases.length ? demo_cases : {};
        this.locations = [
            this.makeLocation(), this.makeLocation(), this.makeLocation(),
        ];
        this.locations_src = [
            this.makeLocation('LOC-SRC'), this.makeLocation('LOC-SRC'), this.makeLocation('LOC-SRC'),
        ];
        this.locations_dst = [
            this.makeLocation('LOC-DST'), this.makeLocation('LOC-DST'), this.makeLocation('LOC-DST'),
        ];
    }

    get_case (key) {
        return this.demo_cases[key];
    }

    add_case (key, demo_case) {
        return this.demo_cases[key] = demo_case;
    }

    // Tools to generate data
    getRandomInt (max) {
        max = max ? max : 10000;
        return Math.floor(Math.random() * Math.floor(max)) + 1;
    }

    batchList (count=5) {
        const list = [];
        for (let i = 1; i < count + 1; i++) {
            list.push({
                "id": i,
                "name": "Batch #" + i,
                "picking_count": this.getRandomInt(3),
                "move_line_count": this.getRandomInt(15),
            });
        }
        return list;
    }

    randomFromArray (an_array) {
        return an_array[Math.floor(Math.random() * an_array.length)];
    }

    makeSimpleRecord (options) {
        const opts = _.defaults(options, {
            'name_prefix': '',
            'padding': 6,
        });
        const name = opts.name_prefix ? opts.name_prefix + '-' : '';
        return {
            "id": this.getRandomInt(),
            "name": name + _.padStart(this.getRandomInt(), opts.padding, 0),
        };
    }

    makeLocation (prefix) {
        return this.makeSimpleRecord({name_prefix: prefix || 'LOC'});
    }

    makeLot () {
        return this.makeSimpleRecord({name_prefix: 'LOT'});
    }

    makePack () {
        const pack = this.makeSimpleRecord({name_prefix: 'PACK', padding: 10});
        _.extend(pack, {
            "package_type": {
                "id": this.getRandomInt(),
                "name": "PKG type " + this.getRandomInt(),
            },
        });
        return pack;
    }

    makeProduct (i) {
        const prod = this.makeSimpleRecord({name_prefix: 'Prod ' + i, padding: 0});
        const default_code = _.padStart(this.getRandomInt(), 8, 0);
        _.extend(prod, {
            "default_code": default_code,
            "display_name": "[" + default_code + "] " + prod.name,
            "qty": this.getRandomInt(200),
            "qty_available": this.getRandomInt(200),
        });
        return prod;
    }

    makePickingLines (options={}) {
        const lines = [];
        for (let i = 1; i < options.lines_count + 1; i++) {
            let pack = this.makePack();
            if (options.line_random_pack && i % 3 == 0) {
                // No pack every 3 items
                pack = null;
            }
            let loc_dst = this.randomFromArray(this.locations_dst);
            if (options.line_random_dst && i % 3 == 0) {
                // No pack every 3 items
                loc_dst = null;
            }
            lines.push({
                "id": i,
                "picking_id": options.picking ? options.picking.id : null,
                "product": this.makeProduct(i),
                "pack": pack,
                "location_src": this.randomFromArray(this.locations_src),
                "location_dst": loc_dst,
            });
        }
        return lines;
    }

    makePicking (options={}) {
        const picking = this.makeSimpleRecord({name_prefix: 'PICK', padding: 8});
        _.extend(picking, {
            "origin": "SO" + _.padStart(this.getRandomInt(), 6, 0),
            "move_line_count": this.getRandomInt(10),
            "weight": this.getRandomInt(1000),
            "lines_count": 0,
        });
        options.picking = picking;
        picking.lines = this.makePickingLines(options);
        return picking;
    }

    makeBatchPickingLine () {
        return {
            "id": this.getRandomInt(),
            "postponed": true,
            "picking": this.makePicking(),
            "batch": this.makeSimpleRecord({name_prefix: 'BATCH'}),
            "lot": this.makeLot(),
            "pack": this.makePack(),
            "origin": "S0" + this.getRandomInt(),
            "move_line_count": this.getRandomInt(20),
            "product": this.makeProduct(),
            "location_src": this.makeLocation('LOC-SRC'),
            "location_dst": this.makeLocation('LOC-DST'),
        };
    }

}

export var demotools = new DemoTools(window.DEMO_CASES || {});
