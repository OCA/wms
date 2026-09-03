
[![Support the OCA](https://odoo-community.org/readme-banner-image)](https://odoo-community.org/get-involved?utm_source=repo-readme)

# Warehouse Management System (WMS)
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/wms&target_branch=14.0)
[![Pre-commit Status](https://github.com/OCA/wms/actions/workflows/pre-commit.yml/badge.svg?branch=14.0)](https://github.com/OCA/wms/actions/workflows/pre-commit.yml?query=branch%3A14.0)
[![Build Status](https://github.com/OCA/wms/actions/workflows/test.yml/badge.svg?branch=14.0)](https://github.com/OCA/wms/actions/workflows/test.yml?query=branch%3A14.0)
[![codecov](https://codecov.io/gh/OCA/wms/branch/14.0/graph/badge.svg)](https://codecov.io/gh/OCA/wms)
[![Translation Status](https://translation.odoo-community.org/widgets/wms-14-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/wms-14-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

WMS modules for Odoo

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[delivery_carrier_preference](delivery_carrier_preference/) | 14.0.1.1.4 |  | Advanced selection of preferred shipping methods
[delivery_carrier_warehouse](delivery_carrier_warehouse/) | 14.0.1.2.0 |  | Get delivery method used in sales orders from warehouse
[delivery_preference_glue_stock_picking_group](delivery_preference_glue_stock_picking_group/) | 14.0.1.0.0 |  | Fix Delivery preferences module on grouping picking
[sale_stock_available_to_promise_release](sale_stock_available_to_promise_release/) | 14.0.1.2.0 |  | Integration between Sales and Available to Promise Release
[sale_stock_available_to_promise_release_cutoff](sale_stock_available_to_promise_release_cutoff/) | 14.0.1.1.1 |  | Cutoff management with respect to stock availability
[sale_stock_available_to_promise_release_dropshipping](sale_stock_available_to_promise_release_dropshipping/) | 14.0.1.0.0 |  | Glue module between sale_stock_available_to_promise_release and stock_dropshipping
[shopfloor](shopfloor/) | 14.0.4.19.2 | <a href='https://github.com/guewen'><img src='https://github.com/guewen.png' width='32' height='32' style='border-radius:50%;' alt='guewen'/></a> <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> <a href='https://github.com/sebalix'><img src='https://github.com/sebalix.png' width='32' height='32' style='border-radius:50%;' alt='sebalix'/></a> | manage warehouse operations with barcode scanners
[shopfloor_base](shopfloor_base/) | 14.0.2.14.0 | <a href='https://github.com/guewen'><img src='https://github.com/guewen.png' width='32' height='32' style='border-radius:50%;' alt='guewen'/></a> <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> <a href='https://github.com/sebalix'><img src='https://github.com/sebalix.png' width='32' height='32' style='border-radius:50%;' alt='sebalix'/></a> | Core module for creating mobile apps
[shopfloor_base_multicompany](shopfloor_base_multicompany/) | 14.0.1.0.0 |  | Provide multi-company support and validation to Shopfloor applications.
[shopfloor_batch_automatic_creation](shopfloor_batch_automatic_creation/) | 14.0.1.2.0 | <a href='https://github.com/guewen'><img src='https://github.com/guewen.png' width='32' height='32' style='border-radius:50%;' alt='guewen'/></a> | Create batch transfers for Cluster Picking
[shopfloor_checkout_package_measurement](shopfloor_checkout_package_measurement/) | 14.0.1.2.0 | <a href='https://github.com/TDu'><img src='https://github.com/TDu.png' width='32' height='32' style='border-radius:50%;' alt='TDu'/></a> | Add a screen on checkout scenario for required package measurements.
[shopfloor_checkout_package_measurement_mobile](shopfloor_checkout_package_measurement_mobile/) | 14.0.1.0.3 |  | Frontend for package measurement on the checkout shopfloor scenario
[shopfloor_checkout_putinpack_restriction](shopfloor_checkout_putinpack_restriction/) | 14.0.1.2.0 | <a href='https://github.com/TDu'><img src='https://github.com/TDu.png' width='32' height='32' style='border-radius:50%;' alt='TDu'/></a> | Shopfloor Checkout Put In Pack Restriction
[shopfloor_checkout_sync](shopfloor_checkout_sync/) | 14.0.1.3.0 | <a href='https://github.com/guewen'><img src='https://github.com/guewen.png' width='32' height='32' style='border-radius:50%;' alt='guewen'/></a> | Glue module
[shopfloor_dangerous_goods](shopfloor_dangerous_goods/) | 14.0.1.1.0 | <a href='https://github.com/mmequignon'><img src='https://github.com/mmequignon.png' width='32' height='32' style='border-radius:50%;' alt='mmequignon'/></a> | Glue Module Between Shopfloor and Stock Dangerous Goods
[shopfloor_dangerous_goods_mobile](shopfloor_dangerous_goods_mobile/) | 14.0.1.1.1 |  | Glue module between Shopfloor Mobile and Shopfloor Dangerous Goods
[shopfloor_delivery_shipment](shopfloor_delivery_shipment/) | 14.0.1.6.0 | <a href='https://github.com/sebalix'><img src='https://github.com/sebalix.png' width='32' height='32' style='border-radius:50%;' alt='sebalix'/></a> <a href='https://github.com/TDu'><img src='https://github.com/TDu.png' width='32' height='32' style='border-radius:50%;' alt='TDu'/></a> | Manage delivery process with shipment advices
[shopfloor_delivery_shipment_mobile](shopfloor_delivery_shipment_mobile/) | 14.0.1.4.0 |  | Frontend for delivery shipment scenario for shopfloor
[shopfloor_example](shopfloor_example/) | 14.0.1.2.0 |  | Show how to customize the Shopfloor app frontend.
[shopfloor_full_location_reservation](shopfloor_full_location_reservation/) | 14.0.1.0.0 | <a href='https://github.com/mt-software-de'><img src='https://github.com/mt-software-de.png' width='32' height='32' style='border-radius:50%;' alt='mt-software-de'/></a> | Adds a configuration to the shopfloor scenario which allows to trigger the stock full location reservation
[shopfloor_location_content_transfer_force_package](shopfloor_location_content_transfer_force_package/) | 14.0.1.1.0 | <a href='https://github.com/TDu'><img src='https://github.com/TDu.png' width='32' height='32' style='border-radius:50%;' alt='TDu'/></a> | Force to select package if location already contains packages.
[shopfloor_manual_product_transfer](shopfloor_manual_product_transfer/) | 14.0.1.5.1 | <a href='https://github.com/sebalix'><img src='https://github.com/sebalix.png' width='32' height='32' style='border-radius:50%;' alt='sebalix'/></a> | Manage manual product transfers
[shopfloor_manual_product_transfer_mobile](shopfloor_manual_product_transfer_mobile/) | 14.0.1.3.1 |  | Frontend for manual product transfer scenario for Shopfloor
[shopfloor_mobile](shopfloor_mobile/) | 14.0.1.41.0 | <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> | Mobile frontend for WMS Shopfloor app
[shopfloor_mobile_base](shopfloor_mobile_base/) | 14.0.3.21.0 | <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> | Mobile frontend for WMS Shopfloor app
[shopfloor_mobile_base_auth_api_key](shopfloor_mobile_base_auth_api_key/) | 14.0.2.1.0 |  | Provides authentication via API key to Shopfloor base mobile app
[shopfloor_mobile_base_auth_user](shopfloor_mobile_base_auth_user/) | 14.0.2.0.1 |  | Provides authentication via standard user login
[shopfloor_packing_info](shopfloor_packing_info/) | 14.0.1.1.0 |  | Allows to predefine packing information messages per partner.
[shopfloor_purchase_base](shopfloor_purchase_base/) | 14.0.1.1.0 | <a href='https://github.com/mt-software-de'><img src='https://github.com/mt-software-de.png' width='32' height='32' style='border-radius:50%;' alt='mt-software-de'/></a> | Module for Shopfloor Purchase Data connection
[shopfloor_reception](shopfloor_reception/) | 14.0.2.12.1 | <a href='https://github.com/mmequignon'><img src='https://github.com/mmequignon.png' width='32' height='32' style='border-radius:50%;' alt='mmequignon'/></a> <a href='https://github.com/JuMiSanAr'><img src='https://github.com/JuMiSanAr.png' width='32' height='32' style='border-radius:50%;' alt='JuMiSanAr'/></a> | Reception scenario for shopfloor
[shopfloor_reception_mobile](shopfloor_reception_mobile/) | 14.0.0.9.0 | <a href='https://github.com/JuMiSanAr'><img src='https://github.com/JuMiSanAr.png' width='32' height='32' style='border-radius:50%;' alt='JuMiSanAr'/></a> | Scenario for receiving products
[shopfloor_reception_packaging_dimension](shopfloor_reception_packaging_dimension/) | 14.0.1.2.0 | <a href='https://github.com/TDu'><img src='https://github.com/TDu.png' width='32' height='32' style='border-radius:50%;' alt='TDu'/></a> | Collect Packaging Dimension from the Reception scenario
[shopfloor_reception_packaging_dimension_mobile](shopfloor_reception_packaging_dimension_mobile/) | 14.0.1.1.0 | <a href='https://github.com/TDu'><img src='https://github.com/TDu.png' width='32' height='32' style='border-radius:50%;' alt='TDu'/></a> | Frontend for the packaging dimension on reception scenario
[shopfloor_reception_purchase_partner_ref](shopfloor_reception_purchase_partner_ref/) | 14.0.1.1.0 | <a href='https://github.com/mt-software-de'><img src='https://github.com/mt-software-de.png' width='32' height='32' style='border-radius:50%;' alt='mt-software-de'/></a> | Adds the purchase partner ref field to shopfloor reception scenario
[shopfloor_reception_purchase_partner_ref_mobile](shopfloor_reception_purchase_partner_ref_mobile/) | 14.0.1.1.0 | <a href='https://github.com/mt-software-de'><img src='https://github.com/mt-software-de.png' width='32' height='32' style='border-radius:50%;' alt='mt-software-de'/></a> | Adds the purchase partner ref field to shopfloor reception scenario
[shopfloor_reception_refund_return](shopfloor_reception_refund_return/) | 14.0.1.0.0 | <a href='https://github.com/mmequignon'><img src='https://github.com/mmequignon.png' width='32' height='32' style='border-radius:50%;' alt='mmequignon'/></a> | Mark created return as to refund
[shopfloor_reception_vendor_packaging](shopfloor_reception_vendor_packaging/) | 14.0.1.0.0 |  | Manage shopfloor reception behavior for vendor packaging
[shopfloor_rest_log](shopfloor_rest_log/) | 14.0.1.2.1 | <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> | Integrate rest_log into Shopfloor app
[shopfloor_single_product_transfer](shopfloor_single_product_transfer/) | 14.0.2.5.0 | <a href='https://github.com/mmequignon'><img src='https://github.com/mmequignon.png' width='32' height='32' style='border-radius:50%;' alt='mmequignon'/></a> | Move an item from one location to another.
[shopfloor_single_product_transfer_force_package](shopfloor_single_product_transfer_force_package/) | 14.0.1.2.0 | <a href='https://github.com/JuMiSanAr'><img src='https://github.com/JuMiSanAr.png' width='32' height='32' style='border-radius:50%;' alt='JuMiSanAr'/></a> | Force to select package if location already contains packages.
[shopfloor_single_product_transfer_mobile](shopfloor_single_product_transfer_mobile/) | 14.0.1.2.0 | <a href='https://github.com/JuMiSanAr'><img src='https://github.com/JuMiSanAr.png' width='32' height='32' style='border-radius:50%;' alt='JuMiSanAr'/></a> | Mobile frontend for single product transfer scenario
[shopfloor_single_product_transfer_unique_order_at_location](shopfloor_single_product_transfer_unique_order_at_location/) | 14.0.1.2.0 | <a href='https://github.com/TDu'><img src='https://github.com/TDu.png' width='32' height='32' style='border-radius:50%;' alt='TDu'/></a> | Prevent to mix sales order on same consolidation location.
[shopfloor_vendor_packaging](shopfloor_vendor_packaging/) | 14.0.1.0.0 |  | Manage shopfloor behavior for vendor packaging
[shopfloor_workstation](shopfloor_workstation/) | 14.0.1.3.1 |  | Manage warehouse workstation with barcode scanners
[shopfloor_workstation_label_printer](shopfloor_workstation_label_printer/) | 14.0.1.1.0 |  | Adds a label printer configuration to the user and shopfloor workstation.
[shopfloor_workstation_mobile](shopfloor_workstation_mobile/) | 14.0.1.0.1 |  | Shopfloor mobile app integration for workstation
[stock_available_to_promise_release](stock_available_to_promise_release/) | 14.0.3.3.2 |  | Release Operations based on available to promise
[stock_available_to_promise_release_dynamic_routing](stock_available_to_promise_release_dynamic_routing/) | 14.0.1.1.0 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Glue between moves release and dynamic routing
[stock_available_to_promise_release_exclude_location](stock_available_to_promise_release_exclude_location/) | 14.0.1.0.0 |  | Exclude locations from available stock
[stock_available_to_promise_release_shipment_advice](stock_available_to_promise_release_shipment_advice/) | 14.0.1.0.0 |  | Glue module between release of operations and shipment advice
[stock_checkout_sync](stock_checkout_sync/) | 14.0.1.1.0 |  | Sync location for Checkout operations
[stock_dynamic_routing](stock_dynamic_routing/) | 14.0.1.1.2 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Dynamic routing of stock moves
[stock_dynamic_routing_checkout_sync](stock_dynamic_routing_checkout_sync/) | 14.0.1.0.0 |  | Glue module for tests when dynamic routing and checkout sync are used
[stock_dynamic_routing_reserve_rule](stock_dynamic_routing_reserve_rule/) | 14.0.1.0.1 |  | Glue module between dynamic routing and reservation rules
[stock_full_location_reservation](stock_full_location_reservation/) | 14.0.1.0.0 | <a href='https://github.com/mt-software-de'><img src='https://github.com/mt-software-de.png' width='32' height='32' style='border-radius:50%;' alt='mt-software-de'/></a> | Extend reservation to full content of location
[stock_full_location_reservation_on_assign](stock_full_location_reservation_on_assign/) | 14.0.1.0.0 | <a href='https://github.com/mt-software-de'><img src='https://github.com/mt-software-de.png' width='32' height='32' style='border-radius:50%;' alt='mt-software-de'/></a> | Do a automatic full location reservationon picking's action_assign
[stock_move_source_relocate](stock_move_source_relocate/) | 14.0.1.3.1 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Change source location of unavailable moves
[stock_move_source_relocate_dynamic_routing](stock_move_source_relocate_dynamic_routing/) | 14.0.1.1.0 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Glue module
[stock_picking_completion_info](stock_picking_completion_info/) | 14.0.1.1.0 |  | Display on current document completion information according to next operations
[stock_picking_consolidation_priority](stock_picking_consolidation_priority/) | 14.0.1.1.0 |  | Raise priority of all transfers for a chain when started
[stock_picking_type_shipping_policy](stock_picking_type_shipping_policy/) | 14.0.1.1.0 |  | Define different shipping policies according to picking type
[stock_picking_type_shipping_policy_group_by](stock_picking_type_shipping_policy_group_by/) | 14.0.1.0.0 |  | Glue module for Picking Type Shipping Policy and Group Transfers by Partner and Carrier
[stock_reception_screen](stock_reception_screen/) | 14.0.1.1.0 |  | Dedicated screen to receive/scan goods.
[stock_reception_screen_measuring_device](stock_reception_screen_measuring_device/) | 14.0.2.0.0 | <a href='https://github.com/gurneyalex'><img src='https://github.com/gurneyalex.png' width='32' height='32' style='border-radius:50%;' alt='gurneyalex'/></a> | Allow to use a measuring device from a reception screen.for packaging measurement
[stock_reception_screen_qty_by_packaging](stock_reception_screen_qty_by_packaging/) | 14.0.1.1.0 |  | Glue module for `stock_product_qty_by_packaging` and `stock_vertical_lift`.
[stock_release_channel](stock_release_channel/) | 14.0.2.3.1 | <a href='https://github.com/sebalix'><img src='https://github.com/sebalix.png' width='32' height='32' style='border-radius:50%;' alt='sebalix'/></a> <a href='https://github.com/mt-software-de'><img src='https://github.com/mt-software-de.png' width='32' height='32' style='border-radius:50%;' alt='mt-software-de'/></a> | Manage workload in WMS with release channels
[stock_service_level](stock_service_level/) | 14.0.1.0.1 | <a href='https://github.com/petrus-v'><img src='https://github.com/petrus-v.png' width='32' height='32' style='border-radius:50%;' alt='petrus-v'/></a> | Manage stock route by service level
[stock_service_level_route](stock_service_level_route/) | 14.0.1.0.0 | <a href='https://github.com/petrus-v'><img src='https://github.com/petrus-v.png' width='32' height='32' style='border-radius:50%;' alt='petrus-v'/></a> | Manage stock rules/routes by service level
[stock_storage_type](stock_storage_type/) | 14.0.1.12.3 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Manage packages and locations storage types
[stock_storage_type_buffer](stock_storage_type_buffer/) | 14.0.1.3.0 |  | Exclude storage locations from put-away if their buffer is full
[stock_storage_type_putaway_abc](stock_storage_type_putaway_abc/) | 14.0.1.0.0 |  | Advanced storage strategy ABC for WMS
[stock_unique_order_per_location](stock_unique_order_per_location/) | 14.0.1.0.0 | <a href='https://github.com/TDu'><img src='https://github.com/TDu.png' width='32' height='32' style='border-radius:50%;' alt='TDu'/></a> | Prevent to mix sales order on same consolidation location.
[stock_warehouse_flow](stock_warehouse_flow/) | 14.0.2.1.1 |  | Configure routing flow for stock moves
[stock_warehouse_flow_delivery_refresh](stock_warehouse_flow_delivery_refresh/) | 14.0.1.0.0 |  | Allow to refresh delivery flow when carrier changes
[stock_warehouse_flow_product_packaging](stock_warehouse_flow_product_packaging/) | 14.0.2.0.0 | <a href='https://github.com/mt-software-de'><img src='https://github.com/mt-software-de.png' width='32' height='32' style='border-radius:50%;' alt='mt-software-de'/></a> | Configure packaging types on routing flows for stock moves
[stock_warehouse_flow_release](stock_warehouse_flow_release/) | 14.0.2.1.0 |  | Warehouse flows integrated with Operation Release

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
