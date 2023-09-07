Got to "Inventory > Settings > Routing Flows".

A routing flow can be seen as a helper to generate a delivery route (like the
warehouse is doing automatically). The new route will get its own rules and
operation types that doesn't overlap with the default ones of the warehouse.

A routing flow is responsible to change the warehouse delivery route of a move
by another one depending on some criterias:

* the initial outgoing operation type (usually the default one)
* the carrier
* a custom domain (applied on the move)

This way you are able to change the route a move will take depending on its
carrier and, for instance, the type or the packaging of the product
you want to ship.

.. image:: https://raw.githubusercontent.com/OCA/wms/14.0/stock_warehouse_flow/static/description/config.png
