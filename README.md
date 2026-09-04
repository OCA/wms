
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
[sale_stock_available_to_promise_release](sale_stock_available_to_promise_release/) | 16.0.1.2.0 |  | Integration between Sales and Available to Promise Release
[sale_stock_available_to_promise_release_block](sale_stock_available_to_promise_release_block/) | 16.0.1.1.1 |  | Block release of deliveries from sales orders.
[sale_stock_release_channel](sale_stock_release_channel/) | 16.0.1.0.0 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Sales Stock Release Channel
[sale_stock_release_channel_delivery](sale_stock_release_channel_delivery/) | 16.0.1.0.0 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Sales Stock Release Channel Delivery
[sale_stock_release_channel_delivery_date](sale_stock_release_channel_delivery_date/) | 16.0.1.1.2 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Compute expected date based on available release channels
[sale_stock_release_channel_partner_by_date](sale_stock_release_channel_partner_by_date/) | 16.0.1.1.0 | <a href='https://github.com/sebalix'><img src='https://github.com/sebalix.png' width='32' height='32' style='border-radius:50%;' alt='sebalix'/></a> | Release channels integration with Sales
[sale_stock_release_channel_partner_by_date_delivery](sale_stock_release_channel_partner_by_date_delivery/) | 16.0.1.1.1 | <a href='https://github.com/sebalix'><img src='https://github.com/sebalix.png' width='32' height='32' style='border-radius:50%;' alt='sebalix'/></a> | Filters channels on sales based on selected carrier.
[shopfloor](shopfloor/) | 16.0.2.26.1 | <a href='https://github.com/guewen'><img src='https://github.com/guewen.png' width='32' height='32' style='border-radius:50%;' alt='guewen'/></a> <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> <a href='https://github.com/sebalix'><img src='https://github.com/sebalix.png' width='32' height='32' style='border-radius:50%;' alt='sebalix'/></a> | manage warehouse operations with barcode scanners
[shopfloor_base](shopfloor_base/) | 16.0.1.2.2 | <a href='https://github.com/guewen'><img src='https://github.com/guewen.png' width='32' height='32' style='border-radius:50%;' alt='guewen'/></a> <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> <a href='https://github.com/sebalix'><img src='https://github.com/sebalix.png' width='32' height='32' style='border-radius:50%;' alt='sebalix'/></a> | Core module for creating mobile apps
[shopfloor_batch_automatic_creation](shopfloor_batch_automatic_creation/) | 16.0.1.2.0 | <a href='https://github.com/guewen'><img src='https://github.com/guewen.png' width='32' height='32' style='border-radius:50%;' alt='guewen'/></a> | Create batch transfers for Cluster Picking
[shopfloor_gs1](shopfloor_gs1/) | 16.0.1.1.1 | <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> <a href='https://github.com/sebalix'><img src='https://github.com/sebalix.png' width='32' height='32' style='border-radius:50%;' alt='sebalix'/></a> | Integrate GS1 barcode scan into Shopfloor app
[shopfloor_mobile](shopfloor_mobile/) | 16.0.1.9.0 | <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> | Mobile frontend for WMS Shopfloor app
[shopfloor_mobile_base](shopfloor_mobile_base/) | 16.0.1.3.0 | <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> | Mobile frontend for WMS Shopfloor app
[shopfloor_mobile_base_auth_api_key](shopfloor_mobile_base_auth_api_key/) | 16.0.1.0.0 |  | Provides authentication via API key to Shopfloor base mobile app
[shopfloor_product_dimension](shopfloor_product_dimension/) | 16.0.1.0.0 | <a href='https://github.com/rousseldenis'><img src='https://github.com/rousseldenis.png' width='32' height='32' style='border-radius:50%;' alt='rousseldenis'/></a> | This module allow to enrich product available details about its dimension in shopfloor
[shopfloor_reception](shopfloor_reception/) | 16.0.1.16.1 | <a href='https://github.com/mmequignon'><img src='https://github.com/mmequignon.png' width='32' height='32' style='border-radius:50%;' alt='mmequignon'/></a> <a href='https://github.com/JuMiSanAr'><img src='https://github.com/JuMiSanAr.png' width='32' height='32' style='border-radius:50%;' alt='JuMiSanAr'/></a> | Reception scenario for shopfloor
[shopfloor_reception_add_packaging](shopfloor_reception_add_packaging/) | 16.0.1.0.0 |  | Enables to add a packaging during Reception scenario in Shopfloor.
[shopfloor_reception_add_packaging_mobile](shopfloor_reception_add_packaging_mobile/) | 16.0.1.0.0 |  | Add a 'create new packaging' button in 'set_quantity' screen of Shopfloor.
[shopfloor_reception_dock](shopfloor_reception_dock/) | 16.0.1.2.0 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> <a href='https://github.com/nicolas-delbovier-acsone'><img src='https://github.com/nicolas-delbovier-acsone.png' width='32' height='32' style='border-radius:50%;' alt='nicolas-delbovier-acsone'/></a> | Add docks info to shopfloor
[shopfloor_reception_dock_mobile](shopfloor_reception_dock_mobile/) | 16.0.1.1.0 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> <a href='https://github.com/nicolas-delbovier-acsone'><img src='https://github.com/nicolas-delbovier-acsone.png' width='32' height='32' style='border-radius:50%;' alt='nicolas-delbovier-acsone'/></a> | Add docks info to picking cards in shopfloor app.
[shopfloor_reception_grn](shopfloor_reception_grn/) | 16.0.1.0.0 |  | Enables to select a reception by scanning its GRN.
[shopfloor_reception_grn_mobile](shopfloor_reception_grn_mobile/) | 16.0.1.0.0 |  | Adds GRN on the receptions cards in Shopfloor Reception.
[shopfloor_reception_helpdesk](shopfloor_reception_helpdesk/) | 16.0.1.0.0 |  | This module allows to create helpdesk tickets in reception scenarios
[shopfloor_reception_helpdesk_mobile](shopfloor_reception_helpdesk_mobile/) | 16.0.1.0.0 |  | This module allows to manage front display for helpdesk management in reception scenario
[shopfloor_reception_mobile](shopfloor_reception_mobile/) | 16.0.1.9.0 | <a href='https://github.com/JuMiSanAr'><img src='https://github.com/JuMiSanAr.png' width='32' height='32' style='border-radius:50%;' alt='JuMiSanAr'/></a> | Scenario for receiving products
[shopfloor_reception_packaging_dimension](shopfloor_reception_packaging_dimension/) | 16.0.1.2.1 | <a href='https://github.com/TDu'><img src='https://github.com/TDu.png' width='32' height='32' style='border-radius:50%;' alt='TDu'/></a> | Collect Packaging Dimension from the Reception scenario
[shopfloor_reception_packaging_dimension_mobile](shopfloor_reception_packaging_dimension_mobile/) | 16.0.1.1.0 | <a href='https://github.com/TDu'><img src='https://github.com/TDu.png' width='32' height='32' style='border-radius:50%;' alt='TDu'/></a> | Frontend for the packaging dimension on reception scenario
[shopfloor_reception_product_barcode](shopfloor_reception_product_barcode/) | 16.0.1.2.1 | <a href='https://github.com/rousseldenis'><img src='https://github.com/rousseldenis.png' width='32' height='32' style='border-radius:50%;' alt='rousseldenis'/></a> | Collect Product Barcode from the Reception scenario
[shopfloor_reception_product_barcode_mobile](shopfloor_reception_product_barcode_mobile/) | 16.0.1.1.0 | <a href='https://github.com/rousseldenis'><img src='https://github.com/rousseldenis.png' width='32' height='32' style='border-radius:50%;' alt='rousseldenis'/></a> | Frontend for the product barcode on reception scenario
[shopfloor_reception_putinpack_restriction](shopfloor_reception_putinpack_restriction/) | 16.0.1.1.0 |  | Restrict the use of packages in shopfloor reception
[shopfloor_reception_refund_return](shopfloor_reception_refund_return/) | 16.0.1.0.0 | <a href='https://github.com/mmequignon'><img src='https://github.com/mmequignon.png' width='32' height='32' style='border-radius:50%;' alt='mmequignon'/></a> | Mark created return as to refund
[shopfloor_rest_log](shopfloor_rest_log/) | 16.0.1.0.0 | <a href='https://github.com/simahawk'><img src='https://github.com/simahawk.png' width='32' height='32' style='border-radius:50%;' alt='simahawk'/></a> | Integrate rest_log into Shopfloor app
[shopfloor_single_product_transfer](shopfloor_single_product_transfer/) | 16.0.1.0.0 | <a href='https://github.com/mmequignon'><img src='https://github.com/mmequignon.png' width='32' height='32' style='border-radius:50%;' alt='mmequignon'/></a> <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> <a href='https://github.com/TDu'><img src='https://github.com/TDu.png' width='32' height='32' style='border-radius:50%;' alt='TDu'/></a> | Move an item from one location to another.
[shopfloor_single_product_transfer_mobile](shopfloor_single_product_transfer_mobile/) | 16.0.1.0.0 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> <a href='https://github.com/TDu'><img src='https://github.com/TDu.png' width='32' height='32' style='border-radius:50%;' alt='TDu'/></a> <a href='https://github.com/mmequignon'><img src='https://github.com/mmequignon.png' width='32' height='32' style='border-radius:50%;' alt='mmequignon'/></a> | Mobile frontend for single product transfer scenario
[shopfloor_workstation](shopfloor_workstation/) | 16.0.1.0.0 |  | Manage warehouse workstation with barcode scanners
[shopfloor_workstation_mobile](shopfloor_workstation_mobile/) | 16.0.1.0.0 |  | Shopfloor mobile app integration for workstation
[stock_available_to_promise_release](stock_available_to_promise_release/) | 16.0.3.9.0 |  | Release Operations based on available to promise
[stock_available_to_promise_release_block](stock_available_to_promise_release_block/) | 16.0.1.1.2 |  | Block Release of Operations
[stock_available_to_promise_release_dynamic_routing](stock_available_to_promise_release_dynamic_routing/) | 16.0.1.0.0 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Glue between moves release and dynamic routing
[stock_available_to_promise_release_exclude_location](stock_available_to_promise_release_exclude_location/) | 16.0.1.0.0 |  | Exclude locations from available stock
[stock_dynamic_routing](stock_dynamic_routing/) | 16.0.1.0.4 |  | Dynamic routing of stock moves
[stock_full_location_reservation](stock_full_location_reservation/) | 16.0.1.1.0 | <a href='https://github.com/mt-software-de'><img src='https://github.com/mt-software-de.png' width='32' height='32' style='border-radius:50%;' alt='mt-software-de'/></a> | Extend reservation to full content of location
[stock_picking_batch_creation](stock_picking_batch_creation/) | 16.0.2.2.0 | <a href='https://github.com/lmignon'><img src='https://github.com/lmignon.png' width='32' height='32' style='border-radius:50%;' alt='lmignon'/></a> <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Create a batch of pickings to be processed all together
[stock_picking_completion_info](stock_picking_completion_info/) | 16.0.1.0.1 |  | Display on current document completion information according to next operations
[stock_picking_type_shipping_policy](stock_picking_type_shipping_policy/) | 16.0.1.0.0 |  | Define different shipping policies according to picking type
[stock_release_channel](stock_release_channel/) | 16.0.3.1.2 | <a href='https://github.com/sebalix'><img src='https://github.com/sebalix.png' width='32' height='32' style='border-radius:50%;' alt='sebalix'/></a> <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> <a href='https://github.com/mt-software-de'><img src='https://github.com/mt-software-de.png' width='32' height='32' style='border-radius:50%;' alt='mt-software-de'/></a> | Manage workload in WMS with release channels
[stock_release_channel_auto_release](stock_release_channel_auto_release/) | 16.0.1.1.0 |  | Add an automatic release mode to the release channel
[stock_release_channel_batch_mode_commercial_partner](stock_release_channel_batch_mode_commercial_partner/) | 16.0.1.0.2 |  | Release pickings into channels by batch of same commercial entity
[stock_release_channel_cutoff](stock_release_channel_cutoff/) | 16.0.1.1.0 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Add the cutoff time to the release channel
[stock_release_channel_delivery](stock_release_channel_delivery/) | 16.0.3.0.0 |  | Add a carrier selection criteria on the release channel
[stock_release_channel_depot](stock_release_channel_depot/) | 16.0.1.0.0 |  | This module allows users to add partner depot to stock release channel.
[stock_release_channel_geoengine](stock_release_channel_geoengine/) | 16.0.2.0.0 |  | Release channel based on geo-localization
[stock_release_channel_partner_by_date](stock_release_channel_partner_by_date/) | 16.0.2.1.0 | <a href='https://github.com/sebalix'><img src='https://github.com/sebalix.png' width='32' height='32' style='border-radius:50%;' alt='sebalix'/></a> <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Set release channels for specific delivery dates
[stock_release_channel_partner_by_date_delivery_window](stock_release_channel_partner_by_date_delivery_window/) | 16.0.1.0.0 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Glue Stock Release Channels for Delivery Dates and Delivery window
[stock_release_channel_partner_by_date_public_holidays](stock_release_channel_partner_by_date_public_holidays/) | 16.0.2.0.0 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Glue Stock Release Channels for Delivery Dates and Public holidays
[stock_release_channel_partner_delivery_window](stock_release_channel_partner_delivery_window/) | 16.0.2.1.0 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Allows to define an end date (and time) on a release channel and propagate it to the concerned pickings
[stock_release_channel_partner_public_holidays](stock_release_channel_partner_public_holidays/) | 16.0.2.1.0 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Add an option to exclude the public holidays when assigning th release channel
[stock_release_channel_plan](stock_release_channel_plan/) | 16.0.1.3.0 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Manage release channel preparation plan
[stock_release_channel_plan_depot](stock_release_channel_plan_depot/) | 16.0.1.0.0 |  | This module allows users to set partner depot on stock release channel preparation plan.
[stock_release_channel_plan_process_end_time](stock_release_channel_plan_process_end_time/) | 16.0.1.1.0 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Glue module between release channel plan and process end time
[stock_release_channel_plan_shipment_lead_time](stock_release_channel_plan_shipment_lead_time/) | 16.0.1.1.0 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Stock release channel plan shipment lead time
[stock_release_channel_process_end_time](stock_release_channel_process_end_time/) | 16.0.1.7.0 | <a href='https://github.com/rousseldenis'><img src='https://github.com/rousseldenis.png' width='32' height='32' style='border-radius:50%;' alt='rousseldenis'/></a> <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Allows to define an end date (and time) on a release channel and propagate it to the concerned pickings
[stock_release_channel_propagate_channel_picking](stock_release_channel_propagate_channel_picking/) | 16.0.1.2.0 |  | Allows to propagate the channel to every picking that is created from the original one.
[stock_release_channel_shipment_advice](stock_release_channel_shipment_advice/) | 16.0.1.2.0 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Plan shipment advices for ready and released pickings
[stock_release_channel_shipment_advice_deliver](stock_release_channel_shipment_advice_deliver/) | 16.0.2.0.2 |  | This module adds an action to the release channel to automate the delivery of its shippings.
[stock_release_channel_shipment_advice_process_end_time](stock_release_channel_shipment_advice_process_end_time/) | 16.0.1.0.0 |  | This module allows to set a delay time (in minutes) between the release channel process end time and the shipment advice arrival to the dock time.
[stock_release_channel_shipment_advice_toursolver](stock_release_channel_shipment_advice_toursolver/) | 16.0.1.1.0 |  | Use TourSolver to plan shipment advices for ready and released pickings
[stock_release_channel_shipment_lead_time](stock_release_channel_shipment_lead_time/) | 16.0.2.1.1 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Release channel with shipment lead time
[stock_release_channel_show_volume](stock_release_channel_show_volume/) | 16.0.1.1.0 |  | Display volumes of stock release channels
[stock_release_channel_show_weight](stock_release_channel_show_weight/) | 16.0.1.1.0 |  | Display weights of stock release channels
[stock_release_channel_warehouse_calendar](stock_release_channel_warehouse_calendar/) | 16.0.1.0.1 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Glue module between release channel and warehouse calendar
[stock_storage_type](stock_storage_type/) | 16.0.2.2.0 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> <a href='https://github.com/rousseldenis'><img src='https://github.com/rousseldenis.png' width='32' height='32' style='border-radius:50%;' alt='rousseldenis'/></a> | Manage packages and locations storage types
[stock_storage_type_putaway_abc](stock_storage_type_putaway_abc/) | 16.0.1.0.0 |  | Advanced storage strategy ABC for WMS
[stock_warehouse_flow](stock_warehouse_flow/) | 16.0.1.1.0 |  | Configure routing flow for stock moves
[stock_warehouse_flow_delivery_refresh](stock_warehouse_flow_delivery_refresh/) | 16.0.1.0.0 |  | Allow to refresh delivery flow when carrier changes
[stock_warehouse_flow_release](stock_warehouse_flow_release/) | 16.0.1.1.0 |  | Warehouse flows integrated with Operation Release

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
