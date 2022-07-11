This module introduces the concept of routing flows in order to manage
different delivery routes for a warehouse.

The default behavior of Odoo allows you to have only one delivery route per
warehouse (with one, two or three steps).
With this module, you are now able to manage multiple delivery routes (having
their own rules and operation types), the right one being selected automatically
based on some criterias, like the carrier and any attribute of the stock move
to process.

This allows you to define a delivery route based on the type of goods to ship,
for instance:

* whole pallet (pick + ship)
* cold chain goods
* dangerous goods

.. image:: https://raw.githubusercontent.com/OCA/wms/14.0/stock_warehouse_flow/static/description/flow.png
