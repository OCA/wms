/* eslint no-use-before-define: 0 */ // --> OFF
var DEMO_SCAN_ANYTHING_PACK = {
    'start' : {
        "data": {
            "show_detail_info": {
                "type": "pack",
                "barcode": "akdlsjf",
                "detail_info": {
                    "id": 192834,
                    "name": "PA92834",
                    "location_src": {
                        "id": 1923,
                        "name":  'B1S08A34',
                    },
                    "location_dst": {
                        "id": 224,
                        "name": 'B1S00A01',
                    },
                    "product": [{"id": 1, "name": 'Ski Thermo Sock', "qty": 36, "lot": "19102403"}, {"id": 123, "name": 'Hiking shoes', "qty": 32, "lot": "1910239"}],
                    "picking": {"id": 1, "name": 'Picking 7'},
                },
            },
        },
        "message": undefined,
    },
};

var DEMO_SCAN_ANYTHING_PRODUCT = {
    'start' : {
        "data": {
            "show_detail_info": {
                "type": "product",
                "barcode": "009932424",
                "detail_info": {
                    "id": 424,
                    "name": "Sun Glasses Cat 4 High Alititude",
                    "image": "http://localhost/web/image?model=product.template&id=16&field=image_128&unique=04022020111236",
                    "lot": "AA8122F41",
                    "expiry_date": "2020-12-01",
                    "default_code": "266009083",
                    "supplier_code": "SUP28342",
                    "packaging": [
                        {"id": 98234, "name": "Box", "qty": 8, "qty_unit": "Unit"},
                        {"id": 98235, "name": "Big Box", "qty": 6, "qty_unit": "Box"},
                        {"id": 98236, "name": "Palette", "qty": 27, "qty_unit": "Big Box"},
                    ],
                },
            },
        },
    },
    "message": undefined,
};
var DEMO_SCAN_ANYTHING_LOCATION_1 = {
    'start' : {
        "data": {
            "show_detail_info": {
                "type": "location",
                "barcode": "283429834",
                "detail_info": {
                    "id": 3231,
                    "codebar": "loc",
                    "name": "CCOROL-01",
                    "parent_name": "SCH/Packing/CCOROL",
                    "products": [
                        {
                            "id": 424,
                            "barcode": "PROD424",
                            "name": "Sun Glasses Cat 4 High Altitude",
                            "pack": {
                                "name": "PID0000008",
                                "barcode": "prod",
                            },
                            "lot": "AA8122F41",
                            "qty_instock": 34,
                            "qty_reserved": 12,
                        },
                        {
                            "id": 421,
                            "name": "Sun Glasses Pro Glazier",
                            "pack": {},
                            "lot": "AA8122F41",
                            "qty_instock": 4,
                            "qty_reserved": 0,
                        },
                    ],
                },
            },
            "message": undefined,
        },
    },
};

var DEMO_SCAN_ANYTHING_LOCATION_2 = {
    'start' : {
        "data": {
            "show_detail_info": {
                "type": "location",
                "barcode": "283429834",
                "detail_info": {
                    "id": 3231,
                    "codebar": "loc",
                    "name": "CCOROL-02",
                    "parent_name": "SCH/Packing/CCOROL",
                    "products": [
                        {
                            "id": 424,
                            "barcode": "PROD111",
                            "name": "Truc",
                            "pack": {
                                "name": "PID0000008",
                                "barcode": "pack",
                            },
                            "lot": "AA8122F41",
                            "qty_instock": 34,
                            "qty_reserved": 12,
                        },
                    ],
                },
            },
            "message": undefined,
        },
    },
};

var DEMO_SCAN_ANYTHING_OPERATION = {
    'start' : {
        "data": {
            "show_detail_info": {
                "type": "operation",
                "barcode": "280009834",
                "detail_info": {
                    "id": 321311,
                    "name": "SCH/OUT/00008",
                    "customer": "BestCooperation SA",
                    "schedule_date": "2020-09-12",
                    "operation_type": "Abroad Delivery Order",
                    "destination_location": "DBACK-03",
                    "source_document": "SO0321",
                    "carrier": "",
                    "priority": 3,
                    "note": "Oh so this could be a really long text, how should it be implemented ?",
                    "moves": [
                        {
                            "id": 424,
                            "name": "Sun Glasses Cat 4 High Altitude",
                            "pack": "PID0000008",
                            "lot": "AA8122F41",
                            "qty": 34,
                        },
                        {
                            "id": 421,
                            "name": "Sun Glasses Pro Glazier",
                            "pack": "PID0000421",
                            "lot": "AA8122F41",
                            "qty_instock": 4,
                            "qty_reserved": 0,
                        },
                    ],
                },
            },
        },
        "message": undefined,
    },
};

window.DEMO_CASES = window.DEMO_CASES || {}
window.DEMO_CASES.scan_anything = {
    "pack": DEMO_SCAN_ANYTHING_PACK,
    "prod": DEMO_SCAN_ANYTHING_PRODUCT,
    "loc1": DEMO_SCAN_ANYTHING_LOCATION_1,
    "loc2": DEMO_SCAN_ANYTHING_LOCATION_2,
    "op": DEMO_SCAN_ANYTHING_OPERATION,
};

/* eslint no-use-before-define: 2 */ // --> ON
