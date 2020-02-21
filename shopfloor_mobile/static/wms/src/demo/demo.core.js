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


var makeBatchPickingLine = function () {
    return {
        "id": getRandomInt(),
        "picking": {
            "id": getRandomInt(),
            "name": "PICK" + _.padStart(getRandomInt(), 8, 0),
            "origin": "SO" + _.padStart(getRandomInt(), 6, 0),
        },
        "batch": {
            "id": getRandomInt(),
            "name": "BATCH" + _.padStart(getRandomInt(), 8, 0),
        },
        "lot": {
            "id": getRandomInt(),
            "name": "LOT" + _.padStart(getRandomInt(), 10, 0),
        },
        "pack": {
            "id": getRandomInt(),
            "name": "PACK" + _.padStart(getRandomInt(), 10, 0),
        },
        "origin": "S0" + getRandomInt(),
        "move_line_count": getRandomInt(20),
        "product": {
            "qty_available": getRandomInt(200),
            "qty": getRandomInt(200),
            "name": "Product " + getRandomInt(),
        },
        "destination_bin": "BIN" + _.padStart(getRandomInt(), 5, 0),
        "location_src": {
            "id": getRandomInt(),
            "name": "LOC-SRC-" + _.padStart(getRandomInt(), 10, 0),
        },
        "location_dst": {
            "id": getRandomInt(),
            "name": "LOC-DST-" + _.padStart(getRandomInt(), 10, 0),
        },
    };
};


window.DEMO_CASES = {}; // Collection
/* eslint no-use-before-define: 2 */ // --> ON
