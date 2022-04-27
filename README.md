
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/wms&target_branch=13.0)
[![Build Status](https://travis-ci.com/OCA/wms.svg?branch=13.0)](https://travis-ci.com/OCA/wms)
[![codecov](https://codecov.io/gh/OCA/wms/branch/13.0/graph/badge.svg)](https://codecov.io/gh/OCA/wms)
[![Translation Status](https://translation.odoo-community.org/widgets/wms-13-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/wms-13-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# WMS - Warehouse Management System

Warehouse Management System for advanced logistics processes with Odoo. Work in progress, tracked in this issue https://github.com/OCA/wms/issues/29

## References

 - The WMS presentation made during Odoo XP 2020 [here](https://docs.google.com/presentation/d/1mYOCAaaVWZtCUDbslwIZyOT9_hHezbWkJVXxu0k01fw/edit) or watch the video [here](https://www.youtube.com/watch?v=Jy4JHBlN7HY)
 - The Barcode App presentation  made during the OCA days 2020 [here](https://docs.google.com/presentation/d/1nTX_fR9V73y1Qquotf3iiom5kvTNZLfj-3DfgirR29I/edit?pli=1#slide=id.p1)

![General module architecture](https://user-images.githubusercontent.com/151794/65694568-5c406e80-e076-11e9-8d1c-37716c0ef4b3.png)


## Dynamic routing of operation

Classify operation depending on where they are reserved, manage handover places, creates different goods flow by carriers. Route explains the steps you want to produce whereas the “picking routing operation” defines how operations are grouped according to their final source
and destination location.

## Packaging management

To better manage the product packaging we need to have them properly defined for each product and classify them by type. Most common type are usually:
 - Retail box
 - Transport box
 - Pallet

It is a basic requirement for improved reservation rules, efficient barcode operation and usage of measurement machines such as Cubiscan for example.

## Put away based on storage type, ABC class and constraints (height, weight,..)

Define storage type on location and attribute storage type on PACK. Storage type can also be define on product packaging to help filling up the info while receiving products.
The idea is that anything getting in the warehouse is given a unique PACK ID with proper storage type and attributes (height, weight, etc..). Product are classified in A,B,C Class as well as location depending on their accessibility for optimized chaotic storage.
Put away will then compute the proper location based on those information.

## Reservation rules by packaging and location

Provide configurable reservation rule by location and packaging type with sequence. Thus allows to drive reservation differently depending on the packaging type to retrieve. For example, pick first pallets from Location A and then boxes from location B. 

It supports several removal strategies: default FIFO/FEFO prefer packaging or empty bin to favor emptying spaces over anything else.

## Virtual reservation and release of operations

Make the final stock reservation when needed, decoupled from the order confirmation while respecting the order of arrival through virtual reservation. Thus also helps to create internal operations such as pick or ship when required only. 

When operation release occurs, only create moves for the goods we have in stocks. This will avoid having backorder in internal warehouse operations (only the delivery order will have one).

## Delivery windows, weekly delivery and cut-off time

Define delivery windows for your customers where they can receive your goods. Setup weekly day of delivery if required. Handle cut-off time by customer depending on where they are.

## Group and consolidate your shipment for several orders

Group several orders into one consolidated shipment by carrier during packing operations.

## Manage replenishment zone

Re-allocate your needs for stocks to drive your replenishment operations within your location (from a pallet storage to a shelving one for example). This allows you to re-allocate a missing stock quantity to a given location to wait for stock there while performing replenishment (technically, it allows to change the source of a stock move to make it hit a stock rule).

## Advanced barcode scanner

Decouple transactional Odoo documents and flows toward an efficient shop-floor process. Do not rely on finding the proper operation to process, but scan location and package to deduce what to do with it. Proceed with operation by machine type or zone rather than Odoo document. Get optimized path computed properly.

Configure your barcode menu, chose which scanning process to apply to each operation, allow to process several operation type within a same barcode menu.

Provide state of the art logistics features to handle zero checks, inventory errors and stock out, etc..

## Warehouse map

Allow to represent the warehouse map precisely by defining relevant attributes and naming convention. Thus will also constitute a per-requisit for having a proper path computed while making an optimized picking tour.

## Interface with measurement machine

Here with Cubiscan, but interface might serve as a base for other brand.

## Interface with vertical automated storage

Provide the proper interface and link to connect vertical lift machines such as Kardex.

## Minimum shelf-life

Ensure a minimum shelf life to your customers.

## Manage dangerous goods

Handle proper attributes and report for dangerous goods handling in respect to EU legislation.

# Reference document

 - Draft of the requirements: https://docs.google.com/document/d/1mct6bFFWJqW01wGFcjc-uQNEjyCxvh6Y9TuFdRhe-b0/edit#heading=h.k0bwq3398e7m
 - OCA Days 2019 presentation: https://docs.google.com/presentation/d/1wTbnkjvbId3lZHTCB-VfNr8pDqAFKC4N4UnoIAQEpbo/edit#slide=id.g61dc817660_0_25
 - Barcode draft RFC document : https://docs.google.com/document/d/1acxlz8W7j4Ljhr2KvcJEUYDInejwjRMq2U9Q91gmEEU/edit
 - Barcode Requirements: https://docs.google.com/presentation/d/1A5TVJXryqod7IwVIl03mDUJIUGzqJ-T2FzSWA90zAvw/edit?disco=AAAAGUSCd54&ts=5e749d4d



<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[delivery_carrier_preference](delivery_carrier_preference/) | 13.0.1.5.0 |  | Advanced selection of preferred shipping methods
[delivery_carrier_warehouse](delivery_carrier_warehouse/) | 13.0.1.2.0 |  | Get delivery method used in sales orders from warehouse
[delivery_preference_glue_stock_picking_group](delivery_preference_glue_stock_picking_group/) | 13.0.1.0.0 |  | Fix Delivery preferences module on grouping picking
[sale_stock_available_to_promise_release](sale_stock_available_to_promise_release/) | 13.0.1.7.0 |  | Integration between Sales and Available to Promise Release
[sale_stock_available_to_promise_release_cutoff](sale_stock_available_to_promise_release_cutoff/) | 13.0.1.0.0 |  | Cutoff management with respect to stock availability
[sale_stock_available_to_promise_release_dropshipping](sale_stock_available_to_promise_release_dropshipping/) | 13.0.1.0.0 |  | Glue module between sale_stock_available_to_promise_release and stock_dropshipping
[shopfloor](shopfloor/) | 13.0.4.13.1 | [![guewen](https://github.com/guewen.png?size=30px)](https://github.com/guewen) [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) [![sebalix](https://github.com/sebalix.png?size=30px)](https://github.com/sebalix) | manage warehouse operations with barcode scanners
[shopfloor_base](shopfloor_base/) | 13.0.1.1.0 | [![guewen](https://github.com/guewen.png?size=30px)](https://github.com/guewen) [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) [![sebalix](https://github.com/sebalix.png?size=30px)](https://github.com/sebalix) | Core module for creating mobile apps
[shopfloor_batch_automatic_creation](shopfloor_batch_automatic_creation/) | 13.0.1.1.0 | [![guewen](https://github.com/guewen.png?size=30px)](https://github.com/guewen) | Create batch transfers for Cluster Picking
[shopfloor_checkout_sync](shopfloor_checkout_sync/) | 13.0.1.0.0 | [![guewen](https://github.com/guewen.png?size=30px)](https://github.com/guewen) | Glue module
[shopfloor_delivery_shipment](shopfloor_delivery_shipment/) | 13.0.1.2.0 | [![sebalix](https://github.com/sebalix.png?size=30px)](https://github.com/sebalix) [![TDu](https://github.com/TDu.png?size=30px)](https://github.com/TDu) | Manage delivery process with shipment advices
[shopfloor_delivery_shipment_mobile](shopfloor_delivery_shipment_mobile/) | 13.0.1.0.0 |  | Frontend for delivery shipment scenario for shopfloor
[shopfloor_example](shopfloor_example/) | 13.0.1.0.1 |  | Show how to customize the Shopfloor app frontend.
[shopfloor_mobile](shopfloor_mobile/) | 13.0.2.5.1 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Mobile frontend for WMS Shopfloor app
[shopfloor_mobile_base](shopfloor_mobile_base/) | 13.0.1.13.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Mobile frontend for WMS Shopfloor app
[shopfloor_packing_info](shopfloor_packing_info/) | 13.0.1.0.0 |  | Allows to predefine packing information messages per partner.
[shopfloor_rest_log](shopfloor_rest_log/) | 13.0.1.2.0 | [![simahawk](https://github.com/simahawk.png?size=30px)](https://github.com/simahawk) | Integrate rest_log into Shopfloor app
[shopfloor_workstation](shopfloor_workstation/) | 13.0.1.1.1 |  | Manage warehouse workstation with barcode scanners
[shopfloor_workstation_mobile](shopfloor_workstation_mobile/) | 13.0.1.0.0 |  | Shopfloor mobile app integration for workstation
[stock_available_to_promise_release](stock_available_to_promise_release/) | 13.0.1.11.1 |  | Release Operations based on available to promise
[stock_available_to_promise_release_dynamic_routing](stock_available_to_promise_release_dynamic_routing/) | 13.0.1.0.1 |  | Glue between moves release and dynamic routing
[stock_checkout_sync](stock_checkout_sync/) | 13.0.1.1.0 |  | Sync location for Checkout operations
[stock_dynamic_routing](stock_dynamic_routing/) | 13.0.1.1.1 |  | Dynamic routing of stock moves
[stock_dynamic_routing_checkout_sync](stock_dynamic_routing_checkout_sync/) | 13.0.1.1.0 |  | Glue module for tests when dynamic routing and checkout sync are used
[stock_dynamic_routing_reserve_rule](stock_dynamic_routing_reserve_rule/) | 13.0.1.0.1 |  | Glue module between dynamic routing and reservation rules
[stock_move_source_relocate](stock_move_source_relocate/) | 13.0.1.1.0 |  | Change source location of unavailable moves
[stock_move_source_relocate_dynamic_routing](stock_move_source_relocate_dynamic_routing/) | 13.0.1.1.2 |  | Glue module
[stock_picking_type_shipping_policy](stock_picking_type_shipping_policy/) | 13.0.1.0.0 |  | Define different shipping policies according to picking type
[stock_picking_type_shipping_policy_group_by](stock_picking_type_shipping_policy_group_by/) | 13.0.1.0.0 |  | Glue module for Picking Type Shipping Policy and Group Transfers by Partner and Carrier
[stock_reception_screen](stock_reception_screen/) | 13.0.1.6.2 |  | Dedicated screen to receive/scan goods.
[stock_reception_screen_measuring_device](stock_reception_screen_measuring_device/) | 13.0.1.0.1 | [![gurneyalex](https://github.com/gurneyalex.png?size=30px)](https://github.com/gurneyalex) | Allow to use a measuring device from a reception screen.for packaging measurement
[stock_reception_screen_mrp_subcontracting](stock_reception_screen_mrp_subcontracting/) | 13.0.1.0.1 |  | Reception screen integrated with subcontracted productions.
[stock_reception_screen_qty_by_packaging](stock_reception_screen_qty_by_packaging/) | 13.0.1.0.0 |  | Glue module for `stock_product_qty_by_packaging` and `stock_vertical_lift`.
[stock_storage_type](stock_storage_type/) | 13.0.1.16.0 |  | Manage packages and locations storage types
[stock_storage_type_buffer](stock_storage_type_buffer/) | 13.0.1.3.0 |  | Exclude storage locations from put-away if their buffer is full
[stock_storage_type_putaway_abc](stock_storage_type_putaway_abc/) | 13.0.2.1.0 |  | Advanced storage strategy ABC for WMS

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
