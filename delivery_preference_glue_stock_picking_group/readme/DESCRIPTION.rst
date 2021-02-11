This module fixes a conflict between the two modules `delivery_carrier_preference`
and `stock_picking_group_by_partner_by_carrier`, that makes the function
`release_available_to_promise` loose the carrier set by default on stock picking
for the backorder left by the release.

A customer has a favorite delivery carrier that is set on his sales orders and
the related stock pickings.
The company can have some preferred carrier based on the weight of a shipping.
When a stock picking is partially released the quantity that can be shipped
should have the corresponding company preferred carrier (if applicable) but
the backorder quantity should keep the customer favorite carrier.

The grouping done by the module `stock_picking_group_by_partner_by_carrier`
breaks this functionality by recreating procurement groups during the release.
