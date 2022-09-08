
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/wms&target_branch=14.0)
[![Pre-commit Status](https://github.com/OCA/wms/actions/workflows/pre-commit.yml/badge.svg?branch=14.0)](https://github.com/OCA/wms/actions/workflows/pre-commit.yml?query=branch%3A14.0)
[![Build Status](https://github.com/OCA/wms/actions/workflows/test.yml/badge.svg?branch=14.0)](https://github.com/OCA/wms/actions/workflows/test.yml?query=branch%3A14.0)
[![codecov](https://codecov.io/gh/OCA/wms/branch/14.0/graph/badge.svg)](https://codecov.io/gh/OCA/wms)
[![Translation Status](https://translation.odoo-community.org/widgets/wms-14-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/wms-14-0/?utm_source=widget)

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
[delivery_carrier_preference](delivery_carrier_preference/) | 14.0.1.1.2 |  | Advanced selection of preferred shipping methods
[delivery_carrier_warehouse](delivery_carrier_warehouse/) | 14.0.1.2.0 |  | Get delivery method used in sales orders from warehouse
[delivery_preference_glue_stock_picking_group](delivery_preference_glue_stock_picking_group/) | 14.0.1.0.0 |  | Fix Delivery preferences module on grouping picking
[sale_stock_available_to_promise_release](sale_stock_available_to_promise_release/) | 14.0.1.1.1 |  | Integration between Sales and Available to Promise Release
[sale_stock_available_to_promise_release_cutoff](sale_stock_available_to_promise_release_cutoff/) | 14.0.1.1.1 |  | Cutoff management with respect to stock availability
[sale_stock_available_to_promise_release_dropshipping](sale_stock_available_to_promise_release_dropshipping/) | 14.0.1.0.0 |  | Glue module between sale_stock_available_to_promise_release and stock_dropshipping
[shopfloor](shopfloor/) | 14.0.2.7.0 | [![guewen](https://github.com/guewen.png?size=30px)](https://github.com/guewen) [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) [![sebalix](https://github.com/sebalix.png?size=30px)](https://github.com/sebalix) | manage warehouse operations with barcode scanners
[shopfloor_base](shopfloor_base/) | 14.0.2.5.0 | [![guewen](https://github.com/guewen.png?size=30px)](https://github.com/guewen) [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) [![sebalix](https://github.com/sebalix.png?size=30px)](https://github.com/sebalix) | Core module for creating mobile apps
[shopfloor_batch_automatic_creation](shopfloor_batch_automatic_creation/) | 14.0.1.1.0 | [![guewen](https://github.com/guewen.png?size=30px)](https://github.com/guewen) | Create batch transfers for Cluster Picking
[shopfloor_checkout_sync](shopfloor_checkout_sync/) | 14.0.1.0.0 | [![guewen](https://github.com/guewen.png?size=30px)](https://github.com/guewen) | Glue module
[shopfloor_delivery_shipment](shopfloor_delivery_shipment/) | 14.0.1.1.2 | [![sebalix](https://github.com/sebalix.png?size=30px)](https://github.com/sebalix) [![TDu](https://github.com/TDu.png?size=30px)](https://github.com/TDu) | Manage delivery process with shipment advices
[shopfloor_delivery_shipment_mobile](shopfloor_delivery_shipment_mobile/) | 14.0.1.0.0 |  | Frontend for delivery shipment scenario for shopfloor
[shopfloor_example](shopfloor_example/) | 14.0.1.2.0 |  | Show how to customize the Shopfloor app frontend.
[shopfloor_manual_product_transfer](shopfloor_manual_product_transfer/) | 14.0.1.2.2 | [![sebalix](https://github.com/sebalix.png?size=30px)](https://github.com/sebalix) | Manage manual product transfers
[shopfloor_manual_product_transfer_mobile](shopfloor_manual_product_transfer_mobile/) | 14.0.1.1.0 |  | Frontend for manual product transfer scenario for Shopfloor
[shopfloor_mobile](shopfloor_mobile/) | 14.0.1.7.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Mobile frontend for WMS Shopfloor app
[shopfloor_mobile_base](shopfloor_mobile_base/) | 14.0.3.5.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Mobile frontend for WMS Shopfloor app
[shopfloor_mobile_base_auth_api_key](shopfloor_mobile_base_auth_api_key/) | 14.0.2.0.0 |  | Provides authentication via API key to Shopfloor base mobile app
[shopfloor_mobile_base_auth_user](shopfloor_mobile_base_auth_user/) | 14.0.2.0.0 |  | Provides authentication via standard user login
[shopfloor_packing_info](shopfloor_packing_info/) | 14.0.1.0.1 |  | Allows to predefine packing information messages per partner.
[shopfloor_rest_log](shopfloor_rest_log/) | 14.0.1.1.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Integrate rest_log into Shopfloor app
[shopfloor_workstation](shopfloor_workstation/) | 14.0.1.2.0 |  | Manage warehouse workstation with barcode scanners
[shopfloor_workstation_label_printer](shopfloor_workstation_label_printer/) | 14.0.1.0.0 |  | Adds a label printer configuration to the user and shopfloor workstation.
[shopfloor_workstation_mobile](shopfloor_workstation_mobile/) | 14.0.1.0.1 |  | Shopfloor mobile app integration for workstation
[stock_available_to_promise_release](stock_available_to_promise_release/) | 14.0.1.1.3 |  | Release Operations based on available to promise
[stock_available_to_promise_release_dynamic_routing](stock_available_to_promise_release_dynamic_routing/) | 14.0.1.0.0 |  | Glue between moves release and dynamic routing
[stock_checkout_sync](stock_checkout_sync/) | 14.0.1.1.0 |  | Sync location for Checkout operations
[stock_dynamic_routing](stock_dynamic_routing/) | 14.0.1.0.2 |  | Dynamic routing of stock moves
[stock_dynamic_routing_checkout_sync](stock_dynamic_routing_checkout_sync/) | 14.0.1.0.0 |  | Glue module for tests when dynamic routing and checkout sync are used
[stock_dynamic_routing_reserve_rule](stock_dynamic_routing_reserve_rule/) | 14.0.1.0.1 |  | Glue module between dynamic routing and reservation rules
[stock_move_source_relocate](stock_move_source_relocate/) | 14.0.1.0.0 |  | Change source location of unavailable moves
[stock_move_source_relocate_dynamic_routing](stock_move_source_relocate_dynamic_routing/) | 14.0.1.0.1 |  | Glue module
[stock_picking_completion_info](stock_picking_completion_info/) | 14.0.1.1.0 |  | Display on current document completion information according to next operations
[stock_picking_consolidation_priority](stock_picking_consolidation_priority/) | 14.0.1.0.2 |  | Raise priority of all transfers for a chain when started
[stock_picking_type_shipping_policy](stock_picking_type_shipping_policy/) | 14.0.1.1.0 |  | Define different shipping policies according to picking type
[stock_picking_type_shipping_policy_group_by](stock_picking_type_shipping_policy_group_by/) | 14.0.1.0.0 |  | Glue module for Picking Type Shipping Policy and Group Transfers by Partner and Carrier
[stock_reception_screen](stock_reception_screen/) | 14.0.1.0.1 |  | Dedicated screen to receive/scan goods.
[stock_reception_screen_measuring_device](stock_reception_screen_measuring_device/) | 14.0.1.0.0 | [![gurneyalex](https://github.com/gurneyalex.png?size=30px)](https://github.com/gurneyalex) | Allow to use a measuring device from a reception screen.for packaging measurement
[stock_reception_screen_qty_by_packaging](stock_reception_screen_qty_by_packaging/) | 14.0.1.1.0 |  | Glue module for `stock_product_qty_by_packaging` and `stock_vertical_lift`.
[stock_storage_type](stock_storage_type/) | 14.0.1.12.0 |  | Manage packages and locations storage types
[stock_storage_type_buffer](stock_storage_type_buffer/) | 14.0.1.3.0 |  | Exclude storage locations from put-away if their buffer is full
[stock_storage_type_putaway_abc](stock_storage_type_putaway_abc/) | 14.0.1.0.0 |  | Advanced storage strategy ABC for WMS

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
