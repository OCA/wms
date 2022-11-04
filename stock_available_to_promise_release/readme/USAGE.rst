When an outgoing transfer would generate chained moves, it will not. The chained
moves need to be released manually. To do so, open "Inventory > Operations >
Stock Allocation", select the moves to release and use "action > Release
Stock Move". A move can be released only if the available to promise quantity is
greater than zero. This quantity is computed as the product's virtual quantity
minus the previous moves in the list (previous being defined by the field
"Priority Date").

This behaviour is activated by stock route by setting the option
"Release based on Available to Promise".

By default, when an outgoing transfer is released, a backorder is created for
the remaining quantities for products not available at release time. This behaviour
can also be changed by stock route by setting the option "No backorder at release".
In such a case, moves created for unavailable products will remain in the original
outgoing picking and no backorder will be created. At the same time, outgoing
picking will not bet set to printed at release time if one move has been created
from a route whith the option "No backorder at release" set.

At the end of the picking process (when the picking is validated) of an outgoing
transfer, if a backorder is created, the chained moves can be automatically
unreleased. This behaviour is activated by setting the option "Unrelease on backorder"
on the stock picking type.
