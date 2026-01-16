
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/wms&target_branch=19.0)
[![Pre-commit Status](https://github.com/OCA/wms/actions/workflows/pre-commit.yml/badge.svg?branch=19.0)](https://github.com/OCA/wms/actions/workflows/pre-commit.yml?query=branch%3A19.0)
[![Build Status](https://github.com/OCA/wms/actions/workflows/test.yml/badge.svg?branch=19.0)](https://github.com/OCA/wms/actions/workflows/test.yml?query=branch%3A19.0)
[![codecov](https://codecov.io/gh/OCA/wms/branch/19.0/graph/badge.svg)](https://codecov.io/gh/OCA/wms)
[![Translation Status](https://translation.odoo-community.org/widgets/wms-19-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/wms-19-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# Warehouse Management System (WMS)

There are several repositories where you can find modules and contribute to.

## Repositories and guidelines

Repository | Description
| --------------------------------- | --- |
[delivery-carrier](https://github.com/OCA/delivery-carrier) | Delivery method providers and all enhancements around delivery method in sales and stock
[product-attribute](https://github.com/OCA/product-attribute) | Extend the product model (incl uom, packaging, pricelist) but that do not touch sales or stock models
[stock-logistics-availability](https://github.com/OCA/stock-logistics-availability) | Compute quantity available in stock
[stock-logistics-barcode](https://github.com/OCA/stock-logistics-barcode) | Product and product packaging barcodes
[stock-logistics-interfaces](https://github.com/OCA/stock-logistics-interfaces) | Interfaces to interact with physical devices (vertical lift, measurement device...)
[stock-logistics-orderpoint](https://github.com/OCA/stock-logistics-orderpoint) | Reordering rules
[stock-logistics-putaway](https://github.com/OCA/stock-logistics-putaway) | Enhance put-away computation for storing goods in stock.
[stock-logistics-release-channel](https://github.com/OCA/stock-logistics-release-channel) | Dispatch management. Organize and dispatch work in the warehouse by release channels
[stock-logistics-reporting](https://github.com/OCA/stock-logistics-reporting) | Stock reportings
[stock-logistics-request](https://github.com/OCA/stock-logistics-request) | Record needs for products
[stock-logistics-reservation](https://github.com/OCA/stock-logistics-reservation) | Enhance the way products are allocated (virtual reservation) and reserved (rules extending fifo) in the stock
[stock-logistics-shopfloor](https://github.com/OCA/stock-logistics-shopfloor) | Shopfloor. Warehouse barcode applications to support operators in the warehouse
[stock-logistics-tracking](https://github.com/OCA/stock-logistics-tracking) | Enhance packages (stock.quant.package)
[stock-logistics-transport](https://github.com/OCA/stock-logistics-transport) | Manage incoming and outgoing transports
[stock-logistics-warehouse](https://github.com/OCA/stock-logistics-warehouse) | Extend the stock related models (warehouse, location, picking, move, lot...) but without impacting flows and processes. It's mainly adding fields or buttons.
[stock-logistics-workflow](https://github.com/OCA/stock-logistics-workflow) | Enhance the way flows and processes are working. Modules that do not have their place in the other more specialized repositories
[stock-weighing](https://github.com/OCA/stock-weighing) | Support products managed by weight
[wms](https://github.com/OCA/wms) | Bundle modules for a complete WMS solution


<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---

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
