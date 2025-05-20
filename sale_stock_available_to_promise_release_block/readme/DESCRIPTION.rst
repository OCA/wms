Block and unblock release of deliveries from sale orders.

Release of deliveries can be blocked right after the sale order confirmation.

When encoding a new order sharing the same delivery address, the user can
list the existing blocked deliveries (backorders) and plan to unblock them
when this new order is confirmed, making the existing deliveries and the new
ones sharing the same scheduled dates and deadlines.

As a side-effect, this will leverage the module
`stock_picking_group_by_partner_by_carrier_by_date` if this one is installed,
by grouping all delivery lines within the same delivery order.
