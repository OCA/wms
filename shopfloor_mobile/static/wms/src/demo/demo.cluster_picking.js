/* eslint no-use-before-define: 0 */  // --> OFF

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
                'records': batchList(15)
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

window.DEMO_CASES["cluster_picking"] = DEMO_CLUSTER_PICKING_1

/* eslint no-use-before-define: 2 */  // --> ON
