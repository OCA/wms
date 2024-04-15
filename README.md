
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
[delivery_carrier_warehouse](delivery_carrier_warehouse/) | 16.0.1.0.1 |  | Get delivery method used in sales orders from warehouse
[sale_stock_available_to_promise_release](sale_stock_available_to_promise_release/) | 16.0.1.0.0 |  | Integration between Sales and Available to Promise Release
[sale_stock_available_to_promise_release_block](sale_stock_available_to_promise_release_block/) | 16.0.1.0.0 |  | Block release of deliveries from sales orders.
[shopfloor_base](shopfloor_base/) | 16.0.1.0.1 | [![guewen](https://github.com/guewen.png?size=30px)](https://github.com/guewen) [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) [![sebalix](https://github.com/sebalix.png?size=30px)](https://github.com/sebalix) | Core module for creating mobile apps
[stock_available_to_promise_release](stock_available_to_promise_release/) | 16.0.3.1.0 |  | Release Operations based on available to promise
[stock_available_to_promise_release_block](stock_available_to_promise_release_block/) | 16.0.1.1.0 |  | Block Release of Operations
[stock_available_to_promise_release_exclude_location](stock_available_to_promise_release_exclude_location/) | 16.0.1.0.0 |  | Exclude locations from available stock
[stock_dynamic_routing](stock_dynamic_routing/) | 16.0.1.0.2 |  | Dynamic routing of stock moves
[stock_picking_completion_info](stock_picking_completion_info/) | 16.0.1.0.1 |  | Display on current document completion information according to next operations
[stock_picking_type_shipping_policy](stock_picking_type_shipping_policy/) | 16.0.1.0.0 |  | Define different shipping policies according to picking type
[stock_release_channel](stock_release_channel/) | 16.0.2.12.0 | [![sebalix](https://github.com/sebalix.png?size=30px)](https://github.com/sebalix) [![jbaudoux](https://github.com/jbaudoux.png?size=30px)](https://github.com/jbaudoux) [![mt-software-de](https://github.com/mt-software-de.png?size=30px)](https://github.com/mt-software-de) | Manage workload in WMS with release channels
[stock_release_channel_auto_release](stock_release_channel_auto_release/) | 16.0.1.0.2 |  | Add an automatic release mode to the release channel
[stock_release_channel_batch_mode_commercial_partner](stock_release_channel_batch_mode_commercial_partner/) | 16.0.1.0.2 |  | Release pickings into channels by batch of same commercial entity
[stock_release_channel_cutoff](stock_release_channel_cutoff/) | 16.0.1.0.2 | [![jbaudoux](https://github.com/jbaudoux.png?size=30px)](https://github.com/jbaudoux) | Add the cutoff time to the release channel
[stock_release_channel_delivery](stock_release_channel_delivery/) | 16.0.2.0.0 |  | Add a carrier selection criteria on the release channel
[stock_release_channel_geoengine](stock_release_channel_geoengine/) | 16.0.1.0.0 |  | Release channel based on geo-localization
[stock_release_channel_partner_delivery_window](stock_release_channel_partner_delivery_window/) | 16.0.1.0.1 | [![jbaudoux](https://github.com/jbaudoux.png?size=30px)](https://github.com/jbaudoux) | Allows to define an end date (and time) on a release channel and propagate it to the concerned pickings
[stock_release_channel_partner_public_holidays](stock_release_channel_partner_public_holidays/) | 16.0.1.0.0 | [![jbaudoux](https://github.com/jbaudoux.png?size=30px)](https://github.com/jbaudoux) | Add an option to exclude the public holidays when assigning th release channel
[stock_release_channel_plan](stock_release_channel_plan/) | 16.0.1.3.0 | [![jbaudoux](https://github.com/jbaudoux.png?size=30px)](https://github.com/jbaudoux) | Manage release channel preparation plan
[stock_release_channel_plan_process_end_time](stock_release_channel_plan_process_end_time/) | 16.0.1.1.0 | [![jbaudoux](https://github.com/jbaudoux.png?size=30px)](https://github.com/jbaudoux) | Glue module between release channel plan and process end time
[stock_release_channel_process_end_time](stock_release_channel_process_end_time/) | 16.0.1.7.0 | [![rousseldenis](https://github.com/rousseldenis.png?size=30px)](https://github.com/rousseldenis) [![jbaudoux](https://github.com/jbaudoux.png?size=30px)](https://github.com/jbaudoux) | Allows to define an end date (and time) on a release channel and propagate it to the concerned pickings
[stock_release_channel_propagate_channel_picking](stock_release_channel_propagate_channel_picking/) | 16.0.1.2.0 |  | Allows to propagate the channel to every picking that is created from the original one.
[stock_release_channel_shipment_advice](stock_release_channel_shipment_advice/) | 16.0.1.1.0 | [![jbaudoux](https://github.com/jbaudoux.png?size=30px)](https://github.com/jbaudoux) | Plan shipment advices for ready and released pickings
[stock_release_channel_shipment_advice_process_end_time](stock_release_channel_shipment_advice_process_end_time/) | 16.0.1.0.0 |  | This module allows to set a delay time (in minutes) between the release channel process end time and the shipment advice arrival to the dock time.
[stock_release_channel_shipment_advice_toursolver](stock_release_channel_shipment_advice_toursolver/) | 16.0.1.0.0 |  | Use TourSolver to plan shipment advices for ready and released pickings
[stock_release_channel_shipment_lead_time](stock_release_channel_shipment_lead_time/) | 16.0.1.2.0 | [![jbaudoux](https://github.com/jbaudoux.png?size=30px)](https://github.com/jbaudoux) | Release channel with shipment lead time
[stock_release_channel_show_volume](stock_release_channel_show_volume/) | 16.0.1.1.0 |  | Display volumes of stock release channels
[stock_release_channel_show_weight](stock_release_channel_show_weight/) | 16.0.1.1.0 |  | Display weights of stock release channels
[stock_storage_type](stock_storage_type/) | 16.0.1.0.7 | [![jbaudoux](https://github.com/jbaudoux.png?size=30px)](https://github.com/jbaudoux) [![rousseldenis](https://github.com/rousseldenis.png?size=30px)](https://github.com/rousseldenis) | Manage packages and locations storage types
[stock_storage_type_putaway_abc](stock_storage_type_putaway_abc/) | 16.0.1.0.0 |  | Advanced storage strategy ABC for WMS
[stock_warehouse_flow](stock_warehouse_flow/) | 16.0.1.0.2 |  | Configure routing flow for stock moves

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
