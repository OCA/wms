/**
 * Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {demotools} from "/shopfloor_mobile_base/static/wms/src/demo/demo.core.js";

const delivery_shipment_menu_id = demotools.addAppMenu({
    name: "Delivery Shipment",
    scenario: "delivery_shipment",
    picking_types: [{id: 27, name: "Random type"}],
});
const pick = demotools.makePicking();
const pack = demotools.makePack();
const shipment = {
    id: 1,
    name: "SA/OUT/0000001",
    state: "confirmed",
    dock: {
        id: 1,
        name: "Dock 01",
    },
};
const lading = [
    demotools.makePicking({load_state: _.sample(["all", "partial", "none"])}),
    demotools.makePicking({load_state: _.sample(["all", "partial", "none"])}),
    demotools.makePicking({load_state: _.sample(["all", "partial", "none"])}),
    demotools.makePicking({load_state: _.sample(["all", "partial", "none"])}),
    demotools.makePicking({load_state: _.sample(["all", "partial", "none"])}),
];
const on_dock = [
    demotools.makePicking({load_state: _.sample(["all", "partial", "none"])}),
    demotools.makePicking({load_state: _.sample(["all", "partial", "none"])}),
    demotools.makePicking({load_state: _.sample(["all", "partial", "none"])}),
    demotools.makePicking({load_state: _.sample(["all", "partial", "none"])}),
    demotools.makePicking({load_state: _.sample(["all", "partial", "none"])}),
];
const DELIVERY_SHIPMENT_CASE = {
    scan_dock: {
        next_state: "scan_document",
        data: {
            scan_document: {
                // picking: _.cloneDeep(pick),
                shipment_advice: _.cloneDeep(shipment),
            },
        },
    },
    scan_document: {
        OP1: {
            next_state: "scan_document",
            message: {
                message_type: "info",
                body: "Operation found",
            },
            data: {
                scan_document: {
                    picking: _.cloneDeep(pick),
                    shipment_advice: _.cloneDeep(shipment),
                },
            },
        },
        PACK1: {
            next_state: "scan_document",
            message: {
                message_type: "info",
                body: "Pack found",
            },
            data: {
                scan_document: {
                    // picking: _.cloneDeep(pick),
                    shipment_advice: _.cloneDeep(shipment),
                    packaging: _.cloneDeep(pack),
                },
            },
        },
        next_state: "loading_list",
        data: {
            loading_list: {
                // picking: _.cloneDeep(pick),
                shipment_advice: _.cloneDeep(shipment),
                lading: lading,
                on_dock: on_dock,
            },
        },
    },
    loading_list: {
        next_state: "validate_shipment",
        // message: {
        //     message_type: "info",
        // body: "Loading list state",
        // },
        data: {
            validate_shipment: {
                // picking: _.cloneDeep(pick),
                shipment_advice: _.cloneDeep(shipment),
            },
        },
    },
    validate_shipment: {
        next_state: "scan_dock",
        message: {
            message_type: "info",
            body: "Shipment ABC has been validated",
        },
        data: {
            scan_dock: {},
        },
    },
};

demotools.add_case("delivery_shipment", DELIVERY_SHIPMENT_CASE);
