Block delivery of unavailable products on backorders.

A blocked delivey cannot be assigned to a release channel.
To unblock such delivery a new order has to be created to get a new move stacked
in the same delivery (thanks to `stock_picking_group_by_partner_by_carrier` module
from `OCA/stock-logistics-workflow` for instance), or the user has to unblock
it manually.
