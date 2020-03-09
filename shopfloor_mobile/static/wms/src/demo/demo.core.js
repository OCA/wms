/* eslint no-use-before-define: 0 */ // --> OFF

var getRandomInt = function (max) {
    max = max ? max : 10000;
    return Math.floor(Math.random() * Math.floor(max)) + 1;
};

var batchList = function (count=5) {
    const list = [];
    for (let i = 1; i < count + 1; i++) {
        list.push({
            "id": i,
            "name": "Batch #" + i,
            "picking_count": getRandomInt(3),
            "move_line_count": getRandomInt(15),
        });
    }
    return list;
};

var randomFromArray = function (an_array) {
    return an_array[Math.floor(Math.random() * an_array.length)];
};


var makeSimpleRecord = function (options) {
    const opts = _.defaults(options, {
        'name_prefix': '',
        'padding': 6,
    });
    const name = opts.name_prefix ? opts.name_prefix + '-' : '';
    return {
        "id": getRandomInt(),
        "name": name + _.padStart(getRandomInt(), opts.padding, 0),
    };
};


var makeLocation = function (prefix) {
    return makeSimpleRecord({name_prefix: prefix || 'LOC'});
};

var makeLot = function () {
    return makeSimpleRecord({name_prefix: 'LOT'});
};

var makePack = function () {
    return makeSimpleRecord({name_prefix: 'PACK', padding: 10});
};

var locations = [makeLocation(), makeLocation(), makeLocation()];
var locations_src = [makeLocation('LOC-SRC'), makeLocation('LOC-SRC'), makeLocation('LOC-SRC')];
var locations_dst = [makeLocation('LOC-DST'), makeLocation('LOC-DST'), makeLocation('LOC-DST')];


var makeProduct = function (i) {
    const prod = makeSimpleRecord({name_prefix: 'Prod ' + i, padding: 0});
    const default_code = _.padStart(getRandomInt(), 8, 0);
    _.extend(prod, {
        "default_code": default_code,
        "display_name": "[" + default_code + "] " + prod.name,
        "qty": getRandomInt(200),
        "qty_available": getRandomInt(200),
    });
    return prod;
};


var makePickingLines = function (options={}) {
    const lines = [];
    for (let i = 1; i < options.lines_count + 1; i++) {
        let pack = makePack();
        if (options.line_random_pack && i % 3 == 0) {
            // No pack every 3 items
            pack = null;
        }
        let loc_dst = randomFromArray(locations_dst);
        if (options.line_random_dst && i % 3 == 0) {
            // No pack every 3 items
            loc_dst = null;
        }
        lines.push({
            "id": i,
            "picking_id": options.picking ? options.picking.id : null,
            "product": makeProduct(i),
            "pack": pack,
            "location_src": randomFromArray(locations_src),
            "location_dst": loc_dst,
        });
    }
    return lines;
};


var makePicking = function (options={}) {
    const picking = makeSimpleRecord({name_prefix: 'PICK', padding: 8});
    _.extend(picking, {
        "origin": "SO" + _.padStart(getRandomInt(), 6, 0),
        "move_line_count": getRandomInt(10),
        "weight": getRandomInt(1000),
        "lines_count": 0,
    });
    options.picking = picking;
    picking.lines = makePickingLines(options);
    return picking;
};


var makeBatchPickingLine = function () {
    return {
        "id": getRandomInt(),
        "postponed": true,
        "picking": makePicking(),
        "batch": makeSimpleRecord({name_prefix: 'BATCH'}),
        "lot": makeLot(),
        "pack": makePack(),
        "origin": "S0" + getRandomInt(),
        "move_line_count": getRandomInt(20),
        "product": makeProduct(),
        "location_src": makeLocation('LOC-SRC'),
        "location_dst": makeLocation('LOC-DST'),
    };
};


window.DEMO_CASES = window.DEMO_CASES || {}; // Collection
/* eslint no-use-before-define: 2 */ // --> ON
