import {process_registry} from "../services/process_registry.js";

export class DemoTools {
    constructor(demo_cases) {
        this.demo_cases = demo_cases.length ? demo_cases : {};
        this.locations = [
            this.makeLocation(),
            this.makeLocation(),
            this.makeLocation(),
        ];
        this.locations_src = [
            this.makeLocation({}, {name_prefix: "LOC-SRC"}),
            this.makeLocation({}, {name_prefix: "LOC-SRC"}),
            this.makeLocation({}, {name_prefix: "LOC-SRC"}),
        ];
        this.locations_dest = [
            this.makeLocation({}, {name_prefix: "LOC-DST"}),
            this.makeLocation({}, {name_prefix: "LOC-DST"}),
            this.makeLocation({}, {name_prefix: "LOC-DST"}),
        ];
        this.packagings = [
            this.makePackaging({
                name: "Little Box",
                qty: 10,
                qty_unit: "Unit",
            }),
            this.makePackaging({
                name: "Box",
                qty: 20,
                qty_unit: "Unit",
            }),
            this.makePackaging({
                name: "Big Box",
                qty: 30,
                qty_unit: "Box",
            }),
            this.makePackaging({
                name: "Pallette",
                qty: 50,
                qty_unit: "Big Box",
            }),
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

    randomFutureDate(days) {
        days = days ? days : this.getRandomInt(30);
        const start = new Date();
        let stop = new Date();
        return stop.setDate(start.getDate() + days);
    }

    batchList(count = 5) {
        const list = [];
        for (let i = 1; i < count + 1; i++) {
            list.push(this.makeBatch({}, {name_prefix: "Batch #" + i}));
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

    makeLocation(defaults = {}, options = {}) {
        _.defaults(options, {
            name_prefix: "LOC ",
        });
        _.defaults(defaults, {
            barcode: "loc1",
        });
        const self = this;
        const loc = this.makeSimpleRecord(defaults, options);
        if (options.full_detail) {
            let products = [];
            _.forEach(
                _.range(1, options.products_count || this.getRandomInt(10)),
                function() {
                    products.push(self.makeProductFullDetail({}, {}));
                }
            );
            _.extend(loc, {
                parent_name: _.sample([
                    "Loc A/ Loc B/ Loc C",
                    "Loc X/ Loc Y/ Loc Z",
                    "Loc Foo/ Loc Bar/ Loc Baz",
                ]),
                products: products,
            });
        }
        return loc;
    }

    makeLot() {
        return this.makeSimpleRecord({}, {name_prefix: "LOT"});
    }

    makePackaging(defaults = {}, options = {}) {
        _.defaults(defaults, {
            name: "Packging",
            qty: 1,
            qty_unit: "Unit",
        });
        return this.makeSimpleRecord(defaults, {});
    }

    makePack(defaults = {}, options = {}) {
        const self = this;
        _.defaults(options, {name_prefix: "PACK", padding: 10});
        _.defaults(defaults, {
            barcode: "pack",
            weight: this.getRandomInt(100) + " Kg",
            packaging_name: this.makePackaging().name,
            move_line_count: this.getRandomInt(10),
        });
        if (options.full_detail) {
            let products = [];
            _.forEach(
                _.range(1, options.products_count || this.getRandomInt(5)),
                function() {
                    products.push(self.makeProductFullDetail({}, {}));
                }
            );
            let pickings = [];
            _.forEach(
                _.range(1, options.pickings_count || this.getRandomInt(3)),
                function() {
                    pickings.push(self.makePicking({}, {no_lines: true}));
                }
            );
            _.defaults(defaults, {
                location_src: _.sample(this.locations_src),
                storage_type: "Storage type XXX", // TODO
                package_type: "Package type XXX", // TODO
                products: products,
                pickings: pickings,
            });
        }
        const pack = this.makeSimpleRecord(defaults, options);
        return pack;
    }

    makeProduct(defaults = {}, options = {}) {
        _.defaults(options, {
            name_prefix: "Prod " + this.getRandomInt(),
            padding: 0,
        });
        const default_code = _.padEnd(
            this.randomFromArray("ABCDEFGHIJK") +
                this.randomFromArray("ABCDEFGHIJK") +
                this.getRandomInt(),
            8,
            0
        );
        _.defaults(defaults, {
            default_code: default_code,
            qty_available: this.getRandomInt(200),
        });
        const prod = this.makeSimpleRecord(defaults, options);
        _.extend(prod, {
            display_name: "[" + default_code + "] " + prod.name,
        });
        return prod;
    }

    makeProductFullDetail(defaults = {}, options = {}) {
        _.defaults(defaults, {
            qty_instock: this.getRandomInt(),
            qty_reserved: this.getRandomInt(),
            expiry_date: "2020-12-01",
            supplier_code: "SUP" + this.getRandomInt(200),
            packagings: _.sampleSize(this.packagings, this.getRandomInt(4)),
            // TODO: load some random images
            image: null,
            barcode: "prod",
        });
        _.defaults(options, {
            full_detail: true,
        });
        return this.makeProduct(defaults, options);
    }

    makePickingLines(defaults = {}, options = {}) {
        _.defaults(defaults, {
            picking: options.picking_auto ? this.makePicking() : null,
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
                    product: this.makeProduct({name: "Prod " + i}),
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
        if (options.full_detail) {
            _.defaults(defaults, {
                schedule_date: this.randomFutureDate(),
                operation_type: "An operation type",
                location_dest: _.sample(this.locations_dest),
                carrier: this.randomFromArray([
                    null,
                    "Carrier 1",
                    "Carrier 2",
                    "Carrier 3",
                ]),
                priority: this.getRandomInt(10),
            });
        }
        _.defaults(options, {
            name_prefix: "PICK",
            padding: 8,
            lines_count: options.lines_count || 0,
        });
        const picking = this.makeSimpleRecord(defaults, options);
        if (!options.no_lines) {
            picking.move_lines = this.makePickingLines({picking: picking}, options);
            picking.lines_count = picking.move_lines.length;
        }
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
            location_src: this.makeLocation({}, {name_prefix: "LOC-SRC"}),
            location_dest: this.makeLocation({}, {name_prefix: "LOC-DST"}),
        });
    }

    makeBatch(defaults = {}, options = {}) {
        _.defaults(defaults, {
            weight: this.getRandomInt(1000) + " Kg",
            move_line_count: this.getRandomInt(20),
        });
        _.defaults(options, {name_prefix: "BATCH", padding: 10});
        const batch = this.makeSimpleRecord(defaults, options);
        return batch;
    }

    makeBatchPickingLine(defaults = {}) {
        _.defaults(defaults, {
            postponed: true,
            picking: this.makePicking(),
            batch: this.makeBatch(),
        });
        return this.makeMoveLine(defaults);
    }

    makeSingleLineOperation() {
        return _.head(this.makePickingLines({}, {picking_auto: true, lines_count: 1}));
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

    makeAppMenu() {
        let menu;
        _.forEach(process_registry.all(), function(component, key) {
            menu.push({
                id: key,
                process: {
                    id: key,
                    code: key,
                },
            });
        });
        return menu;
    }
}

export var demotools = new DemoTools(window.DEMO_CASES || {});
