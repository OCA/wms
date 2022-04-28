/**
 * Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * @author Juan Miguel Sánchez Arce <juan.sanchez@camptocamp.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {demotools} from "/shopfloor_mobile_base/static/wms/src/demo/demo.core.js";

const DEMO_CASE = {
    by_menu_id: {},
};

const example_menu_case = demotools.addAppMenu(
    {
        name: "Partner management (demo)",
        scenario: "partner_example",
    },
    "pmgmt_demo"
);

const partners = demotools.partnerNames();
const example_partners_records = partners.map((partner, index) => {
    const record = demotools.makeSimpleRecord({
        name: partner,
        id: index + 1,
    });
    demotools.index_record("id", record, "partner");
    return record;
});

const DEMO_CASE_1 = {
    partner_list: {
        data: {
            listing: {
                records: example_partners_records,
            },
        },
        next_state: "listing",
    },
};

// detail/<int> mock endpoints
example_partners_records.forEach((partner) => {
    const key = "detail/" + partner.id;
    DEMO_CASE_1[key] = _create_partner_detail_endpoint(partner);
});

// scan/<int> mock endpoints
Object.entries(demotools.indexed).forEach(([key, value]) => {
    if (value.type !== "partner") return;
    const case_key = "scan/" + key;
    const partner = value.record;
    DEMO_CASE_1[case_key] = _create_partner_detail_endpoint(partner);
});

function _create_partner_detail_endpoint(partner) {
    let email;
    if (partner.id % 2) {
        email = demotools.makePartnerEmail(partner);
    }
    return {
        next_state: "detail",
        data: {
            detail: {
                record: {
                    email,
                    id: partner.id,
                    name: partner.name,
                    ref: partner.id.toString(),
                },
            },
        },
    };
}

DEMO_CASE.by_menu_id[example_menu_case] = DEMO_CASE_1;

demotools.add_case("partner_example", DEMO_CASE);
