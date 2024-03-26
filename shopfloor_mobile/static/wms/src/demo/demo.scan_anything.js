/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Thierry Ducrest <thierry.ducrest@camptocamp.com>
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {demotools} from "/shopfloor_mobile_base/static/wms/src/demo/demo.core.js";

const DEMO_SCAN_ANYTHING_PACK1 = {
    data: {
        type: "package",
        barcode: "pack",
        record: demotools.makePackFullDetail({}, {}),
    },
};

const DEMO_SCAN_ANYTHING_PACK2 = {
    data: {
        type: "package",
        barcode: "pack2",
        record: demotools.makePackFullDetail({}, {}),
    },
};

const DEMO_SCAN_ANYTHING_PACK3 = {
    data: {
        type: "package",
        barcode: "pack3",
        record: demotools.makePackFullDetail({}, {}),
    },
};

const DEMO_SCAN_ANYTHING_PRODUCT = {
    data: {
        type: "product",
        barcode: "009932424",
        record: demotools.makeProductFullDetail(),
    },
};
const DEMO_SCAN_ANYTHING_PRODUCT_2 = {
    data: {
        type: "product",
        barcode: "prod2",
        record: demotools.makeProductFullDetail(),
    },
};
const DEMO_SCAN_ANYTHING_LOCATION_1 = {
    data: {
        type: "location",
        barcode: "loc1",
        record: demotools.makeLocation({}, {full_detail: true}),
    },
};

const DEMO_SCAN_ANYTHING_LOCATION_2 = {
    data: {
        type: "location",
        barcode: "283429834",
        record: demotools.makeLocation({}, {full_detail: true}),
    },
};

const DEMO_SCAN_ANYTHING_TRANSFER = {
    data: {
        type: "transfer",
        barcode: "transf",
        record: demotools.makePicking({}, {full_detail: true}),
    },
};
const DEMO_SCAN_ANYTHING_TRANSFER1 = {
    data: {
        type: "transfer",
        barcode: "transf1",
        record: demotools.makePicking({}, {full_detail: true}),
    },
};
const DEMO_SCAN_ANYTHING_TRANSFER2 = {
    data: {
        type: "transfer",
        barcode: "transf2",
        record: demotools.makePicking({}, {full_detail: true}),
    },
};

const DEMO_SCAN_ANYTHING_LOT = {
    data: {
        type: "lot",
        barcode: "lot",
        record: demotools.makeLotFullDetail(),
    },
};

const DEMO_SCAN_ANYTHING_LOT1 = {
    data: {
        type: "lot",
        barcode: "lot1",
        record: demotools.makeLotFullDetail(),
    },
};
const DEMO_SCAN_ANYTHING_LOT2 = {
    data: {
        type: "lot",
        barcode: "lot2",
        record: demotools.makeLotFullDetail(),
    },
};

demotools.add_case("scan_anything", {
    pack: DEMO_SCAN_ANYTHING_PACK1,
    pack2: DEMO_SCAN_ANYTHING_PACK2,
    pack3: DEMO_SCAN_ANYTHING_PACK3,
    prod: DEMO_SCAN_ANYTHING_PRODUCT,
    prod2: DEMO_SCAN_ANYTHING_PRODUCT_2,
    loc: DEMO_SCAN_ANYTHING_LOCATION_1,
    loc2: DEMO_SCAN_ANYTHING_LOCATION_2,
    tr: DEMO_SCAN_ANYTHING_TRANSFER,
    tr1: DEMO_SCAN_ANYTHING_TRANSFER1,
    tr2: DEMO_SCAN_ANYTHING_TRANSFER2,
    lot: DEMO_SCAN_ANYTHING_LOT,
    lot1: DEMO_SCAN_ANYTHING_LOT1,
    lot2: DEMO_SCAN_ANYTHING_LOT2,
    // TODO: not found
});
