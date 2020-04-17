export class DemoTools {
    constructor(demo_cases) {
        this.demo_cases = demo_cases.length ? demo_cases : {};
        this.locations = [
            this.makeLocation(),
            this.makeLocation(),
            this.makeLocation(),
        ];
        this.locations_src = [
            this.makeLocation("LOC-SRC"),
            this.makeLocation("LOC-SRC"),
            this.makeLocation("LOC-SRC"),
        ];
        this.locations_dest = [
            this.makeLocation("LOC-DST"),
            this.makeLocation("LOC-DST"),
            this.makeLocation("LOC-DST"),
        ];
    }

    get_case(key) {
        return this.demo_cases[key];
    }

    add_case(key, demo_case) {
        return (this.demo_cases[key] = demo_case);
    }

    // Tools to generate data
    getRandomInt(max) {
        max = max ? max : 10000;
        return Math.floor(Math.random() * Math.floor(max)) + 1;
    }

    batchList(count = 5) {
        const list = [];
        for (let i = 1; i < count + 1; i++) {
            list.push({
                id: i,
                name: "Batch #" + i,
                picking_count: this.getRandomInt(3),
                move_line_count: this.getRandomInt(15),
            });
        }
        return list;
    }

    randomFromArray(an_array) {
        return an_array[Math.floor(Math.random() * an_array.length)];
    }

    makeSimpleRecord(defaults = {}, options = {}) {
        _.defaults(options, {
            name_prefix: "",
            padding: 6,
        });
        let name = defaults.name;
        if (!name) {
            name = options.name_prefix ? options.name_prefix + "-" : "";
            name += _.padStart(this.getRandomInt(), options.padding, 0);
        }
        return _.defaults(defaults, {
            id: this.getRandomInt(),
            name: name,
        });
    }

    makeLocation(prefix) {
        return this.makeSimpleRecord({}, {name_prefix: prefix || "LOC"});
    }

    makeLot() {
        return this.makeSimpleRecord({}, {name_prefix: "LOT"});
    }

    makePack(options = {}) {
        _.extend(options, {name_prefix: "PACK", padding: 10});
        const pack = this.makeSimpleRecord({}, options);
        _.extend(pack, {
            weight: this.getRandomInt(100) + " Kg",
            packaging_name: "PKG type " + this.getRandomInt(10),
            move_line_count: this.getRandomInt(10),
        });
        return pack;
    }

    makeProduct(i = 0) {
        i = i != 0 ? i : this.getRandomInt();
        const prod = this.makeSimpleRecord({}, {name_prefix: "Prod " + i, padding: 0});
        const default_code = _.padEnd(
            this.randomFromArray("ABCDEFGHIJK") +
                this.randomFromArray("ABCDEFGHIJK") +
                this.getRandomInt(),
            8,
            0
        );
        _.extend(prod, {
            default_code: default_code,
            display_name: "[" + default_code + "] " + prod.name,
            // TODO: check if still needed
            qty: this.getRandomInt(200),
            qty_available: this.getRandomInt(200),
        });
        return prod;
    }

    makePickingLines(defaults = {}, options = {}) {
        _.defaults(defaults, {
            picking: null,
        });
        const lines = [];
        for (let i = 1; i < options.lines_count + 1; i++) {
            let pack = this.makePack();
            if (options.line_random_pack && i % 3 == 0) {
                // No pack every 3 items
                pack = null;
            }
            let loc_dest = this.randomFromArray(this.locations_dest);
            if (options.line_random_dest && i % 3 == 0) {
                // No pack every 3 items
                loc_dest = null;
            }
            let line = _.defaults(
                this.makeMoveLine({
                    id: i,
                    product: this.makeProduct(i),
                    package_dest: pack,
                    location_src: this.randomFromArray(this.locations_src),
                    location_dest: loc_dest,
                }),
                defaults
            );
            lines.push(line);
        }
        return lines;
    }

    makePicking(defaults = {}, options = {}) {
        _.defaults(defaults, {
            origin: "SO" + _.padStart(this.getRandomInt(), 6, 0),
            move_line_count: this.getRandomInt(10),
            weight: this.getRandomInt(1000),
            partner: this.makeSimpleRecord({
                name: this.randomFromArray(this.customerNames()),
            }),
            note: this.randomFromArray([null, "demo picking note"]),
        });
        _.defaults(options, {
            name_prefix: "PICK",
            padding: 8,
            lines_count: options.lines_count || 0,
        });
        const picking = this.makeSimpleRecord(defaults, options);
        picking.move_lines = this.makePickingLines({picking: picking}, options);
        picking.lines_count = picking.move_lines.length;
        return picking;
    }

    makeMoveLine(defaults = {}, options = {}) {
        _.defaults(defaults, {
            qty_done: 0,
        });
        _.defaults(options, {
            qty_done_random: true,
        });
        const qty = this.getRandomInt(100);
        let qty_done = options.qty_done_full ? qty : defaults.qty_done;
        qty_done = options.qty_done_random ? this.getRandomInt(qty) : qty_done;
        return _.defaults({}, defaults, {
            id: this.getRandomInt(),
            quantity: qty,
            qty_done: qty_done,
            product: this.makeProduct(),
            lot: this.makeLot(),
            package_src: this.makePack({name_prefix: "PACK-SRC"}),
            package_dest: this.makePack({name_prefix: "PACK-DST"}),
            origin: "S0" + this.getRandomInt(),
            location_src: this.makeLocation("LOC-SRC"),
            location_dest: this.makeLocation("LOC-DST"),
        });
    }

    makeBatchPickingLine(defaults = {}) {
        _.defaults(defaults, {
            postponed: true,
            picking: this.makePicking(),
            batch: this.makeSimpleRecord({}, {name_prefix: "BATCH"}),
        });
        return this.makeMoveLine(defaults);
    }

    customerNames() {
        return [
            "Edith Sanchez",
            "Brandon Freeman",
            "Nicole Ford",
            "Willie Burke",
            "Ron Gibson",
            "Toni Rhodes",
            "Gemini Furniture",
            "Ready Mat",
            "The Jackson Group",
            "Azure Interior",
            "Joel Willis",
            "Julie Richards",
            "Travis Mendoza",
            "Billy Fox",
            "Jesse Brown",
            "Kim Snyder",
            "Douglas Fletcher",
            "Floyd Steward",
            "Edwin Hansen",
            "Soham Palmer",
            "Gordon Owens",
            "Oscar Morgan",
            "Lorraine Douglas",
            "Addison Olson",
            "Sandra Neal",
            "Colleen Diaz",
            "Tom Ruiz",
            "Theodore Gardner",
            "Wood Corner",
            "Deco Addict",
            "Dwayne Newman",
            "Chester Reed",
            "Lumber Inc",
            "Jeff Lawson",
            "Marc Demo",
        ];
    }
}

export var demotools = new DemoTools(window.DEMO_CASES || {});
