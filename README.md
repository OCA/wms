[![Runbot Status](https://runbot.odoo-community.org/runbot/badge/flat/285/13.0.svg)](https://runbot.odoo-community.org/runbot/repo/github-com-oca-wms-285)
[![Build Status](https://travis-ci.com/OCA/wms.svg?branch=13.0)](https://travis-ci.com/OCA/wms)
[![codecov](https://codecov.io/gh/OCA/wms/branch/13.0/graph/badge.svg)](https://codecov.io/gh/OCA/wms)
[![Translation Status](https://translation.odoo-community.org/widgets/wms-13-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/wms-13-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# WMS

Warehouse Management System for advance logistic with Odoo

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | summary
--- | --- | ---
[delivery_carrier_preference](delivery_carrier_preference/) | 13.0.1.5.0 | Advanced selection of preferred shipping methods
[delivery_carrier_warehouse](delivery_carrier_warehouse/) | 13.0.1.2.0 | Get delivery method used in sales orders from warehouse
[delivery_preference_glue_stock_picking_group](delivery_preference_glue_stock_picking_group/) | 13.0.1.0.0 | Fix Delivery preferences module on grouping picking
[sale_stock_available_to_promise_release](sale_stock_available_to_promise_release/) | 13.0.1.5.0 | Integration between Sales and Available to Promise Release
[shopfloor](shopfloor/) | 13.0.4.4.3 | manage warehouse operations with barcode scanners
[shopfloor_base](shopfloor_base/) | 13.0.1.1.0 | Core module for creating mobile apps
[shopfloor_batch_automatic_creation](shopfloor_batch_automatic_creation/) | 13.0.1.0.2 | Create batch transfers for Cluster Picking
[shopfloor_checkout_sync](shopfloor_checkout_sync/) | 13.0.1.0.0 | Glue module
[shopfloor_example](shopfloor_example/) | 13.0.1.0.0 | Show how to customize the Shopfloor app frontend.
[shopfloor_mobile](shopfloor_mobile/) | 13.0.2.2.3 | Mobile frontend for WMS Shopfloor app
[shopfloor_mobile_base](shopfloor_mobile_base/) | 13.0.1.10.1 | Mobile frontend for WMS Shopfloor app
[shopfloor_packing_info](shopfloor_packing_info/) | 13.0.1.0.0 | Allows to predefine packing information messages per partner.
[shopfloor_rest_log](shopfloor_rest_log/) | 13.0.1.0.1 | Integrate rest_log into Shopfloor app
[shopfloor_workstation](shopfloor_workstation/) | 13.0.1.1.1 | Manage warehouse workstation with barcode scanners
[shopfloor_workstation_mobile](shopfloor_workstation_mobile/) | 13.0.1.0.0 | Shopfloor mobile app integration for workstation
[stock_available_to_promise_release](stock_available_to_promise_release/) | 13.0.1.11.1 | Release Operations based on available to promise
[stock_available_to_promise_release_dynamic_routing](stock_available_to_promise_release_dynamic_routing/) | 13.0.1.0.1 | Glue between moves release and dynamic routing
[stock_checkout_sync](stock_checkout_sync/) | 13.0.1.1.0 | Sync location for Checkout operations
[stock_dynamic_routing](stock_dynamic_routing/) | 13.0.1.1.0 | Dynamic routing of stock moves
[stock_dynamic_routing_checkout_sync](stock_dynamic_routing_checkout_sync/) | 13.0.1.1.0 | Glue module for tests when dynamic routing and checkout sync are used
[stock_dynamic_routing_reserve_rule](stock_dynamic_routing_reserve_rule/) | 13.0.1.0.1 | Glue module between dynamic routing and reservation rules
[stock_move_source_relocate](stock_move_source_relocate/) | 13.0.1.1.0 | Change source location of unavailable moves
[stock_move_source_relocate_dynamic_routing](stock_move_source_relocate_dynamic_routing/) | 13.0.1.1.1 | Glue module
[stock_picking_type_shipping_policy](stock_picking_type_shipping_policy/) | 13.0.1.0.0 | Define different shipping policies according to picking type
[stock_picking_type_shipping_policy_group_by](stock_picking_type_shipping_policy_group_by/) | 13.0.1.0.0 | Glue module for Picking Type Shipping Policy and Group Transfers by Partner and Carrier
[stock_reception_screen](stock_reception_screen/) | 13.0.1.6.2 | Dedicated screen to receive/scan goods.
[stock_storage_type](stock_storage_type/) | 13.0.1.12.0 | Manage packages and locations storage types
[stock_storage_type_buffer](stock_storage_type_buffer/) | 13.0.1.2.0 | Exclude storage locations from put-away if their buffer is full
[stock_storage_type_putaway_abc](stock_storage_type_putaway_abc/) | 13.0.1.1.0 | Advanced storage strategy ABC for WMS

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to OCA
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----

OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
