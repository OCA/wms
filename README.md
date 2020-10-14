[![Runbot Status](https://runbot.odoo-community.org/runbot/badge/flat/285/13.0.svg)](https://runbot.odoo-community.org/runbot/repo/github-com-oca-wms-285)
[![Build Status](https://travis-ci.com/OCA/wms.svg?branch=13.0)](https://travis-ci.com/OCA/wms)
[![codecov](https://codecov.io/gh/OCA/wms/branch/13.0/graph/badge.svg)](https://codecov.io/gh/OCA/wms)

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



----

OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.
