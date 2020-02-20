/* eslint no-use-before-define: 0 */  // --> OFF
var CANCEL_MSG_DEFAULT = {
    'message': 'Operation cancelled',
    'message_type': 'info',
}

var DEMO_SINGLE_PUTAWAY_1 = {
    'start' : {
        "data": {
            "scan_location": {
                "id": 1,
                "name": "A nice pack 1",
                "location_src": {
                    "id": 1,
                    "name":  'Location SRC 1',
                },
                "location_dst": {
                    "id": 2,
                    "name": 'Location SRC 2',
                },
                "product": [{"id": 1, "name": 'Product 1', "qty": 5}, {"id": 2, "name": 'Product 2', "qty": 2}],
                "picking": {"id": 1, "name": 'Picking 1'},
            }
        },
        "next_state": "scan_location",
        "message": undefined
    },
    'validate' : {
        "data": undefined,
        "next_state": "start_scan_pack",
        "message": {
            'message': 'Pack validated',
            'message_type': 'info',
        }
    },
    'cancel' : {
        "next_state": "start",
        "message": CANCEL_MSG_DEFAULT
    }
}

var DEMO_SINGLE_PUTAWAY_2 = {
    'start' : {
        "data": undefined,
        "next_state": "start_scan_pack",
        "message": {"message_type": "error", "message": "You cannot do that!"}
    },
}
var DEMO_SINGLE_PUTAWAY_3 = {
    'start' : {
        "data": undefined,
        "next_state": "start_scan_pack",
        "message": {"message_type": "error", "message": "No pkg found"}
    },
}
var DEMO_SINGLE_PUTAWAY_4 = {
    'start' : {
        "data": {
            "confirm_start": {
                "id": 1,
                "name": "A nice pack 4",
                "location_src": {
                    "id": 1,
                    "name":  'Location SRC 4',
                },
                "location_dst": {
                    "id": 2,
                    "name": 'Location DST 4',
                },
                "product": {"id": 1, "name": 'Product 4'},
                "picking": {"id": 1, "name": 'Picking 4'},
            },
        },
        "next_state": "confirm_start",
        "message": {"message_type": "info", "message": "Benoit is at the toilette: do you take over?"}
    },
    'validate' : {
        "data": undefined,
        "next_state": "start_scan_pack",
        "message": {
            'message': 'Pack validated',
            'message_type': 'info',
        }
    },
    'cancel' : {
        "next_state": "start",
        "message": CANCEL_MSG_DEFAULT
    }
}
var DEMO_SINGLE_PUTAWAY_5 = {
    'start' : {
        "data": {
            "scan_location": {
                "id": 1,
                "name": "A nice pack 5",
                "location_src": {
                    "id": 1,
                    "name":  'Location SRC 5',
                },
                "location_dst": {
                    "id": 2,
                    "name": 'Location DST 5',
                },
                "product": {"id": 1, "name": 'Product 5'},
                "picking": {"id": 1, "name": 'Picking 5'},
            },
        },
        "next_state": "scan_location",
        "message": undefined
    },
    'cancel' : {
        "next_state": "start",
        "message": CANCEL_MSG_DEFAULT
    },
    'validate' : {
        "data": undefined,
        "next_state": "start_scan_pack",
        "message": {
            'message': 'Pack validated',
            'message_type': 'info',
        }
    },
}
var DEMO_SINGLE_PUTAWAY_6 = {
    'start' : {
        "data": {
            "scan_location": {
                "id": 1,
                "name": "A nice pack 6",
                "location_src": {
                    "id": 1,
                    "name":  'Location SRC 6',
                },
                "location_dst": {
                    "id": 2,
                    "name": 'Location DST 6',
                },
                "product": {"id": 1, "name": 'Product 6'},
                "picking": {"id": 1, "name": 'Picking 6'},
            },
        },
        "next_state": "scan_location",
        "message": undefined
    },
    'validate' : {
        "data": undefined,
        "next_state": "confirm_location",
        "message": {"message_type": "warning", "message": "Are you sure of this location?"}
    },
    'LOC6' : {
        "data": undefined,
        "next_state": "start_scan_pack",
        "message": {
            'message': 'Pack validated',
            'message_type': 'info',
        }
    },
}
var DEMO_SINGLE_PUTAWAY_7 = {
    'start' : {
        "data": {
            "scan_location": {
                "id": 1,
                "name": "A nice pack 7",
                "location_src": {
                    "id": 1,
                    "name":  'Location SRC 7',
                },
                "location_dst": {
                    "id": 2,
                    "name": 'Location DST 7',
                },
                "product": {"id": 1, "name": 'Product 7'},
                "picking": {"id": 1, "name": 'Picking 7'},
            },
        },
        "next_state": "scan_location",
        "message": undefined
    },
    'validate' : {
        "data": undefined,
        "next_state": "scan_location",
        "message": {"message_type": "error", "message": "You cannot move to this location"}
    },
    'LOC7' : {
        "data": undefined,
        "next_state": "start_scan_pack",
        "message": {
            'message': 'Pack validated',
            'message_type': 'info',
        }
    },
}

var PACK_1 = {
    "id": 192834,
    "name": "PA92834",
    "location_src": {
        "id": 1923,
        "barcode": "LOC1923",
        "name":  'B1S08A34',
    },
    "location_dst": {
        "id": 224,
        "barcode": "LOC224",
        "name": 'B1S00A01',
    },
    "product": [
        {"id": 1, "name": 'Ski Thermo Sock', "qty": 36, "lot": "19102403"},
        {"id": 123, "name": 'Hiking shoes', "qty": 32, "lot": "1910239"},
    ],
    "picking": {"id": 1, "name": 'Picking 7'},
}

var DEMO_SCAN_ANYTHING_PACK = {
    'start' : {
        "data": {
            "show_detail_info": {
                "type": "pack",
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
        "message": undefined
    },
}
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
            }
        }
    },
    "message": undefined
}
var DEMO_SCAN_ANYTHING_LOCATION = {
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
                            "barcode": "pack",
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
            }
        },
        "message": undefined
    }
    },
}

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
                }
            },
        },
        "message": undefined
    },
}

var DEMO_SINGLE_PACK_TRANSFER_1 = {
    'start' : {
        "data": {
            "scan_location": {
                "type": "pack",
                "id": 1,
                "name": "A nice pack 1",
                "location_src": {
                    "id": 1,
                    "name":  'Location SRC 1',
                },
                "location_dst": {
                    "id": 2,
                    "name": 'Location SRC 2',
                },
                "product": [{"id": 1, "name": 'Product 1', "qty": 5}, {"id": 2, "name": 'Product 2', "qty": 2}],
                "picking": {"id": 1, "name": 'Picking 1'},
            },
        },
        "next_state": "scan_location",
        "message": undefined
    },
    'validate' : {
        "data": undefined,
        "next_state": "start",
        "message": {
            'message': 'Pack validated',
            'message_type': 'info',
        }
    },
    'cancel' : {
        "next_state": "start",
        "message": CANCEL_MSG_DEFAULT
    },
    'LOC1' : {
        "data": undefined,
        "next_state": "start",
        "message": {
            'message': 'Pack validated',
            'message_type': 'info',
        }
    },
    'LOC2' : {
        "data": {
            "show_completion_info": {
                'last_operation_name': 'Last operation XYZ',
                'next_operation_name': 'Next operation XYZ',
            },
        },
        "next_state": "show_completion_info",
        "message": {}
    },
    'LOC3' : {
        "data": undefined,
        "next_state": "start",
        "message": {
            'message': 'Pack validated',
            'message_type': 'info',
        }
    },
}


var getRandomInt = function (max) {
    return Math.floor(Math.random() * Math.floor(max));
}

var batchList = function (count=5) {
    let list = []
    for (let i = 1; i < count + 1; i++) {
        list.push({
            "id": i,
            "name": 'Batch #' + i,
            "picking_count": getRandomInt(3),
            "move_line_count": getRandomInt(15),
        })
    }
    return list
}

var DEMO_CLUSTER_PICKING_1 = {
    'find_batch': {
        'next_state': 'confirm_start',
        'data': {
            'confirm_start': {
                'id': 100,
                'name': 'BATCH001',
                'picking_count': 3,
                'move_line_count': 6,
                'records': [
                    {
                        'id': 1,
                        'name': 'OP001',
                        'customer': {
                            'name': 'Customer 1',
                        },
                        'ref': 'SO000CUST001',
                        'move_line_count': 4,
                    },
                    {
                        'id': 2,
                        'name': 'OP002',
                        'customer': {
                            'name': 'Customer 2',
                        },
                        'ref': 'SO000CUST002',
                        'move_line_count': 2,
                    },
                ]
            }
        }
    },
    'list_batches': {
        'next_state': 'manual_selection',
        'message': {
            'message_type': 'info',
            'message': 'Previous line postponed',
        },
        'data': {
            // next line to process
            'manual_selection': {
                'records': batchList()
            }
        }
    },
    'select': {
        'next_state': 'confirm_start',
        'data': {
            'confirm_start': {
                'id': 100,
                'name': 'BATCHXXX',
                'picking_count': 3,
                'move_line_count': 6,
                'records': [
                    {
                        'id': 1,
                        'name': 'OP001',
                        'customer': {
                            'name': 'Customer 1',
                        },
                        'ref': 'SO000CUST001',
                        'move_line_count': 4,
                    },
                    {
                        'id': 2,
                        'name': 'OP002',
                        'customer': {
                            'name': 'Customer 2',
                        },
                        'ref': 'SO000CUST002',
                        'move_line_count': 2,
                    },
                ]
            }
        }
    },
    'confirm_start': {
        'next_state': 'start_line',
        'data': {
            'start_line': {
                'id': 1,
                'name': 'OP001',
                'customer': {
                    'name': 'Customer 1',
                },
                'ref': 'SO000CUST001',
                'move_line_count': 4,
                'pack': {
                    'qty_on_hand': 5,
                    'qty': 5,
                    'name': 'Karton',
                    'lot': 'THELOT000131'
                },
                'destination_bin': 'Bin #1',
                "location_src": {
                    "id": 1,
                    "name":  'Location SRC 1',
                },
                "location_dst": {
                    "id": 2,
                    "name": 'Location SRC 2',
                },
                "product": {"id": 1, "name": 'Product 4'},
            }
        }
    },
    'unassign': {
        'next_state': 'start',
    },
    'scan_line': {
        'next_state': 'scan_destination',
        'data': {
            'scan_destination': {

            },
        },
    },
    'scan_destination_pack': {
        'ok': {
            'next_state': 'start_line',
            'message': {
                'message_type': 'info',
                'message': 'Product 5 put in bin #2',
            },
            'data': {
                // next line to process
                'start_line': {
                    'id': 2,
                    'name': 'OP001',
                    'customer': {
                        'name': 'Customer 1',
                    },
                    'ref': 'SO000CUST001',
                    'move_line_count': 4,
                    'pack': {
                        'qty_on_hand': 10,
                        'qty': 10,
                        'name': 'Karton',
                        'lot': 'THELOT000131'
                    },
                    'destination_bin': 'Bin #2',
                    "location_src": {
                        "id": 1,
                        "name":  'Location SRC 2',
                    },
                    "location_dst": {
                        "id": 2,
                        "name": 'Location DST 2',
                    },
                    "product": {"id": 1, "name": 'Product 5'},
                },
            },
        },
        'ko': {
            'next_state': 'zero_check',
            'message': {
                'message_type': 'info',
                'message': 'Stock check required',
            },
            'data': {
                'zero_check': {}
            },
        },
    },
    'stock_is_zero': {
        'next_state': 'start_line',
        'message': {
            'message_type': 'info',
            'message': 'Stock zero confirmed',
        },
        'data': {
            // next line to process
            'start_line': {
                'id': 2,
                'name': 'OP001',
                'customer': {
                    'name': 'Customer 1',
                },
                'ref': 'SO000CUST001',
                'move_line_count': 4,
                'pack': {
                    'qty_on_hand': 10,
                    'qty': 10,
                    'name': 'Karton',
                    'lot': 'THELOT000131'
                },
                'destination_bin': 'Bin #2',
                "location_src": {
                    "id": 1,
                    "name":  'Location SRC 2',
                },
                "location_dst": {
                    "id": 2,
                    "name": 'Location DST 2',
                },
                "product": {"id": 1, "name": 'Product 5'},
            },
        },
    },
    'skip_line': {
        'next_state': 'start_line',
        'message': {
            'message_type': 'info',
            'message': 'Previous line postponed',
        },
        'data': {
            // next line to process
            'start_line': {
                'id': 5,
                'name': 'OP005',
                'customer': {
                    'name': 'Customer 4',
                },
                'ref': 'SO000CUST001',
                'move_line_count': 3,
                'pack': {
                    'qty_on_hand': 10,
                    'qty': 10,
                    'name': 'Karton',
                    'lot': 'THELOT000131'
                },
                'destination_bin': 'Bin #2',
                "location_src": {
                    "id": 1,
                    "name":  'Location SRC 2',
                },
                "location_dst": {
                    "id": 2,
                    "name": 'Location DST 2',
                },
                "product": {"id": 1, "name": 'Product 5'},
            },
        },
    },
    'stock_issue': {
        'next_state': 'start_line',
        'message': {
            'message_type': 'info',
            'message': 'Stock out confirmed',
        },
        'data': {
            // next line to process
            'start_line': {
                'id': 5,
                'name': 'OP005',
                'customer': {
                    'name': 'Customer 4',
                },
                'ref': 'SO000CUST001',
                'move_line_count': 3,
                'pack': {
                    'qty_on_hand': 10,
                    'qty': 10,
                    'name': 'Karton',
                    'lot': 'THELOT000131'
                },
                'destination_bin': 'Bin #2',
                "location_src": {
                    "id": 1,
                    "name":  'Location SRC 2',
                },
                "location_dst": {
                    "id": 2,
                    "name": 'Location DST 2',
                },
                "product": {"id": 1, "name": 'Product 5'},
            },
        },
    },
    'check_pack_lot': {},
    'prepare_unload': {
        'next_state': 'unload_all',
        'data': {
            // next line to process
            'unload_all': {}
        },
    },
    'set_destination_all': {
        'OK': {
            'next_state': 'start_line',
            'message': {
                'message_type': 'info',
                'message': 'Destination set',
            },
            'data': {
                // next line to process
                'start_line': {
                    'id': 3,
                    'name': 'OP003',
                    'customer': {
                        'name': 'Customer 3',
                    },
                    'ref': 'SO000CUST001',
                    'move_line_count': 4,
                    'pack': {
                        'qty_on_hand': 10,
                        'qty': 10,
                        'name': 'Karton',
                        'lot': 'THELOT000131'
                    },
                    'destination_bin': 'Bin #2',
                    "location_src": {
                        "id": 1,
                        "name":  'Location SRC 2',
                    },
                    "location_dst": {
                        "id": 2,
                        "name": 'Location DST 2',
                    },
                    "product": {"id": 1, "name": 'Product 5'},
                },
            },
        },
        'KO': {
            'next_state': 'confirm_unload_all',
            'data': {
                // next line to process
                'unload_all': {}
            },
            'message': {
                'message_type': 'warning',
                'message': 'Confirm you want to unload them all?',
            },
        },
    },
    'unload_split': {},
    'unload_scan_pack': {},
    'unload_scan_destination': {},
    'unload_router': {},
}

window.DEMO_SINGLE_PUTAWAY = {
    "1": DEMO_SINGLE_PUTAWAY_1,
    "2": DEMO_SINGLE_PUTAWAY_2,
    "3": DEMO_SINGLE_PUTAWAY_3,
    "4": DEMO_SINGLE_PUTAWAY_4,
    "5": DEMO_SINGLE_PUTAWAY_5,
    "6": DEMO_SINGLE_PUTAWAY_6,
    "7": DEMO_SINGLE_PUTAWAY_7,
}
window.DEMO_SINGLE_PACK_TRANSFER = {
    "PACK1": DEMO_SINGLE_PACK_TRANSFER_1,
    "LOC1": DEMO_SINGLE_PACK_TRANSFER_1,
}
window.DEMO_SCAN_ANYTHING = {
    "pack": DEMO_SCAN_ANYTHING_PACK,
    "prod": DEMO_SCAN_ANYTHING_PRODUCT,
    "loc": DEMO_SCAN_ANYTHING_LOCATION,
    "op": DEMO_SCAN_ANYTHING_OPERATION,
}
window.DEMO_CLUSTER_PICKING = DEMO_CLUSTER_PICKING_1

window.DEMO_CASES = {
    "single_pack_putaway": window.DEMO_SINGLE_PUTAWAY,
    "single_pack_transfer": window.DEMO_SINGLE_PACK_TRANSFER,
    "cluster_picking": window.DEMO_CLUSTER_PICKING,
    "scan_anything": window.DEMO_SCAN_ANYTHING,
}
window.DEMO_CASE = {}

/* eslint no-use-before-define: 2 */  // --> ON
