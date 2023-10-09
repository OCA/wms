
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/wms&target_branch=16.0)
[![Pre-commit Status](https://github.com/OCA/wms/actions/workflows/pre-commit.yml/badge.svg?branch=16.0)](https://github.com/OCA/wms/actions/workflows/pre-commit.yml?query=branch%3A16.0)
[![Build Status](https://github.com/OCA/wms/actions/workflows/test.yml/badge.svg?branch=16.0)](https://github.com/OCA/wms/actions/workflows/test.yml?query=branch%3A16.0)
[![codecov](https://codecov.io/gh/OCA/wms/branch/16.0/graph/badge.svg)](https://codecov.io/gh/OCA/wms)
[![Translation Status](https://translation.odoo-community.org/widgets/wms-16-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/wms-16-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# wms

WMS modules for Odoo

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[stock_available_to_promise_release](stock_available_to_promise_release/) | 16.0.2.2.0 |  | Release Operations based on available to promise
[stock_dynamic_routing](stock_dynamic_routing/) | 16.0.1.0.2 |  | Dynamic routing of stock moves
[stock_picking_completion_info](stock_picking_completion_info/) | 16.0.1.0.1 |  | Display on current document completion information according to next operations
[stock_picking_type_shipping_policy](stock_picking_type_shipping_policy/) | 16.0.1.0.0 |  | Define different shipping policies according to picking type
[stock_release_channel](stock_release_channel/) | 16.0.2.4.1 | [![sebalix](https://github.com/sebalix.png?size=30px)](https://github.com/sebalix) | Manage workload in WMS with release channels
[stock_release_channel_auto_release](stock_release_channel_auto_release/) | 16.0.1.0.1 |  | Add an automatic release mode to the release channel
[stock_release_channel_batch_mode_commercial_partner](stock_release_channel_batch_mode_commercial_partner/) | 16.0.1.0.1 |  | Release pickings into channels by batch of same commercial entity
[stock_release_channel_cutoff](stock_release_channel_cutoff/) | 16.0.1.0.0 | [![jbaudoux](https://github.com/jbaudoux.png?size=30px)](https://github.com/jbaudoux) | Add the cutoff time to the release channel
[stock_release_channel_partner_public_holidays](stock_release_channel_partner_public_holidays/) | 16.0.1.0.0 | [![jbaudoux](https://github.com/jbaudoux.png?size=30px)](https://github.com/jbaudoux) | Add an option to exclude the public holidays when assigning th release channel
[stock_release_channel_process_end_time](stock_release_channel_process_end_time/) | 16.0.1.0.0 | [![rousseldenis](https://github.com/rousseldenis.png?size=30px)](https://github.com/rousseldenis) | Allows to define an end date (and time) on a release channel and propagate it to the concerned pickings
[stock_release_channel_shipment_advice](stock_release_channel_shipment_advice/) | 16.0.1.0.0 | [![jbaudoux](https://github.com/jbaudoux.png?size=30px)](https://github.com/jbaudoux) | Plan shipment advices for ready and released pickings
[stock_release_channel_shipment_lead_time](stock_release_channel_shipment_lead_time/) | 16.0.1.0.0 | [![jbaudoux](https://github.com/jbaudoux.png?size=30px)](https://github.com/jbaudoux) | Release channel with shipment lead time
[stock_storage_type](stock_storage_type/) | 16.0.1.0.3 |  | Manage packages and locations storage types
[stock_storage_type_putaway_abc](stock_storage_type_putaway_abc/) | 16.0.1.0.0 |  | Advanced storage strategy ABC for WMS
[stock_warehouse_flow](stock_warehouse_flow/) | 16.0.1.0.0 |  | Configure routing flow for stock moves

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
