[![Runbot Status](https://runbot.odoo-community.org/runbot/badge/flat/285/14.0.svg)](https://runbot.odoo-community.org/runbot/repo/github-com-oca-wms-285)
[![Build Status](https://travis-ci.com/OCA/wms.svg?branch=14.0)](https://travis-ci.com/OCA/wms)
[![codecov](https://codecov.io/gh/OCA/wms/branch/14.0/graph/badge.svg)](https://codecov.io/gh/OCA/wms)
[![Translation Status](https://translation.odoo-community.org/widgets/wms-14-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/wms-14-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# wms

The WMS repo hosts the major components of the WMS stack for Odoo. Note that some odule have been placed in stock-logistics-* repos as well depending on the context.

## References

 - The WMS presentation made during Odoo XP 2020 [here](https://docs.google.com/presentation/d/1mYOCAaaVWZtCUDbslwIZyOT9_hHezbWkJVXxu0k01fw/edit) or watch the video [here](https://www.youtube.com/watch?v=Jy4JHBlN7HY)
 - The Barcode App presentation  made during the OCA days 2020 [here](https://docs.google.com/presentation/d/1nTX_fR9V73y1Qquotf3iiom5kvTNZLfj-3DfgirR29I/edit?pli=1#slide=id.p1)

## Dynamic routing of operation

**Main module: stock_dynamic_routing***

Classify operation depending on where they are reserved, manage handover places, creates different goods flow by carriers. Route explains the steps you want to produce whereas the “picking routing operation” defines how operations are grouped according to their final source
and destination location.

## Advanced barcode scanner

**Main modules: shopfloor***

Decouple transnational Odoo documents and flows toward an efficient shop-floor process. Do not rely on finding the proper operation to process, but scan location and package to deduce what to do with it. Proceed with operation by machine type or zone rather than Odoo document. Get optimized path computed properly.

Configure your barcode menu, chose which scanning process to apply to each operation, allow to process several operation type within a same barcode menu.

Provide state of the art logistics features to handle zero checks, inventory errors and stock out, etc..

## Put away based on storage type and constraints (height, weight,..)

**Main module: stock_storage_type***

Define storage type on location and attribute storage type on PACK. Storage type can also be define on product packaging to help filling up the info while receiving products.
The idea is that anything getting in the warehouse is given a unique PACK ID with proper storage type and attributes (height, weight, etc..). Put away will then compute the proper location based on those information.

## Virtual reservation and release of operations

**Main module: stock_available_to_promise_release**

Make the final stock reservation when needed, decoupled from the order confirmation while respecting the order of arrival through virtual reservation. Thus also help to create internal operations such as pick or ship when required only. 

When operation release occurs, only create moves for the goods we have in stocks. This will avoid having backorder in internal warehouse operations (only the delivery order will have ones),

## Reception screen

**Main module: stock_reception_screen**

Drive the reception steps in a step-by-step approach and label each logistic unit with a unique serial number (SSCC: Serial Shipping Container Code) as recommended by the GS1 standard.

## Delivery carrier preferences

**Main module: delivery_carrier***

Dynamically (re) assign the best suited carrier to a shipment based on availability of the goods at release of operation time.

# Related work hosted on other OCA repos

Some works initiated by the WMS is hosted in other OCA repos.

## Packaging management

**Main module: product_packaging_type**

To better manage the product packaging we need to have them properly defined for each product and classify them by type. Most common type are usually:
 - Retail box
 - Transport box
 - Pallet

It is a basic requirement for improved reservation rules, efficient barcode operation and usage of measurement machines such as Cubiscan for example.

## Reservation rules by packaging and location

**Main module: stock_reserve_rule**

Provide configurable reservation rule by location and packaging type with sequence. Thus allows to drive reservation differently depending on the packaging type to retrieve. For example, pick first pallets from Location A and then boxes from location B. 

It supports several removal strategies: default FIFO/FEFO prefer packaging or empty bin to favor emptying spaces over anything else.


## Delivery windows, weekly delivery and cut-off time

**Main module: sale_partner_delivery_window* **

Define delivery windows for your customers where they can receive your goods. Setup weekly day of delivery if required. Handle cut-off time by customer depending on where they are.

## Group and consolidate your shipment for several orders

**Main module: stock_picking_group_by_partner_by_carrier***

Group several orders into one consolidated shipment by carrier during packing operations.

## Manage replenishment zone

**Main module: ddmrp***

Re-allocate your needs for stocks to drive your replenishment operations within your location (from a pallet storage to a shelving one for example). This allows you to re-allocate a missing stock quantity to a given location to wait for stock there while performing replenishment (technically, it allows to change the source of a stock move to make it hit a stock rule).

## Interface with measurement machine

**Main module: stock_cubiscan**

Here with Cubiscan, but interface might serve as a base for other brand.

## Interface with vertical automated storage

**Main module: stock_vertical_lift***

Provide the proper interface and link to connect vertical lift machines such as Kardex.

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | summary
--- | --- | ---
[delivery_carrier_warehouse](delivery_carrier_warehouse/) | 14.0.1.2.0 | Get delivery method used in sales orders from warehouse
[shopfloor](shopfloor/) | 14.0.1.0.0 | manage warehouse operations with barcode scanners
[shopfloor_base](shopfloor_base/) | 14.0.1.0.1 | Core module for creating mobile apps
[shopfloor_mobile](shopfloor_mobile/) | 14.0.1.0.1 | Mobile frontend for WMS Shopfloor app
[shopfloor_mobile_base](shopfloor_mobile_base/) | 14.0.1.0.1 | Mobile frontend for WMS Shopfloor app
[shopfloor_workstation](shopfloor_workstation/) | 14.0.1.1.0 | Manage warehouse workstation with barcode scanners
[stock_dynamic_routing](stock_dynamic_routing/) | 14.0.1.0.0 | Dynamic routing of stock moves
[stock_picking_completion_info](stock_picking_completion_info/) | 14.0.1.0.0 | Display on current document completion information according to next operations
[stock_picking_consolidation_priority](stock_picking_consolidation_priority/) | 14.0.1.0.1 | Raise priority of all transfers for a chain when started
[stock_picking_type_shipping_policy_group_by](stock_picking_type_shipping_policy_group_by/) | 14.0.1.0.0 | Glue module for Picking Type Shipping Policy and Group Transfers by Partner and Carrier
[stock_storage_type](stock_storage_type/) | 14.0.1.7.0 | Manage packages and locations storage types
[stock_storage_type_buffer](stock_storage_type_buffer/) | 14.0.1.2.0 | Exclude storage locations from put-away if their buffer is full


Unported addons
---------------
addon | version | summary
--- | --- | ---
[delivery_carrier_preference](delivery_carrier_preference/) | 13.0.1.5.0 (unported) | Advanced selection of preferred shipping methods
[sale_stock_available_to_promise_release](sale_stock_available_to_promise_release/) | 13.0.1.3.0 (unported) | Integration between Sales and Available to Promise Release
[shopfloor_batch_automatic_creation](shopfloor_batch_automatic_creation/) | 13.0.1.0.0 (unported) | Create batch transfers for Cluster Picking
[shopfloor_checkout_sync](shopfloor_checkout_sync/) | 13.0.1.0.0 (unported) | Glue module
[shopfloor_mobile_custom_example](shopfloor_mobile_custom_example/) | 13.0.1.0.0 (unported) | Show how to customize the Shopfloor app frontend.
[stock_available_to_promise_release](stock_available_to_promise_release/) | 13.0.1.9.2 (unported) | Release Operations based on available to promise
[stock_available_to_promise_release_dynamic_routing](stock_available_to_promise_release_dynamic_routing/) | 13.0.1.0.1 (unported) | Glue between moves release and dynamic routing
[stock_move_source_relocate](stock_move_source_relocate/) | 13.0.1.0.0 (unported) | Change source location of unavailable moves
[stock_move_source_relocate_dynamic_routing](stock_move_source_relocate_dynamic_routing/) | 13.0.1.0.0 (unported) | Glue module
[stock_picking_type_shipping_policy](stock_picking_type_shipping_policy/) | 13.0.1.0.0 (unported) | Define different shipping policies according to picking type
[stock_reception_screen](stock_reception_screen/) | 13.0.1.1.2 (unported) | Dedicated screen to receive/scan goods.
[stock_storage_type_putaway_abc](stock_storage_type_putaway_abc/) | 13.0.1.1.0 (unported) | Advanced storage strategy ABC for WMS

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
