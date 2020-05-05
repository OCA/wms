import {demotools} from "./demo.core.js";

const DEMO_SCAN_ANYTHING_PACK = {
    data: {
        type: "pack",
        barcode: "akdlsjf",
        detail_info: demotools.makePack({}, {full_detail: true}),
    },
};

const DEMO_SCAN_ANYTHING_PRODUCT = {
    data: {
        type: "product",
        barcode: "009932424",
        detail_info: demotools.makeProductFullDetail(),
    },
};
const DEMO_SCAN_ANYTHING_PRODUCT_2 = {
    data: {
        type: "product",
        barcode: "prod2",
        detail_info: demotools.makeProductFullDetail(),
    },
};
const DEMO_SCAN_ANYTHING_LOCATION_1 = {
    data: {
        type: "location",
        barcode: "loc1",
        detail_info: demotools.makeLocation({}, {full_detail: true}),
    },
};

const DEMO_SCAN_ANYTHING_LOCATION_2 = {
    data: {
        type: "location",
        barcode: "283429834",
        detail_info: demotools.makeLocation({}, {full_detail: true}),
    },
};

const DEMO_SCAN_ANYTHING_OPERATION = {
    data: {
        type: "operation",
        barcode: "280009834",
        detail_info: demotools.makePicking({}, {full_detail: true}),
    },
};

demotools.add_case("scan_anything", {
    pack: DEMO_SCAN_ANYTHING_PACK,
    prod: DEMO_SCAN_ANYTHING_PRODUCT,
    prod2: DEMO_SCAN_ANYTHING_PRODUCT_2,
    loc1: DEMO_SCAN_ANYTHING_LOCATION_1,
    loc2: DEMO_SCAN_ANYTHING_LOCATION_2,
    op: DEMO_SCAN_ANYTHING_OPERATION,
});
