This module does not add a new user action: it changes what happens when an
operator uses one of the existing stock issue actions (Zone Picking and
Cluster Picking: the "Declare stock issue" action on a line; Location
Content Transfer: "stock out" on a line or a package), once "Loss
Declaration" is selected as the Stock issue strategy on the menu (see
Configuration).

Instead of immediately correcting the inventory, the quant is locked behind
a move of the warehouse's "Loss" operation type (blocking it from being
reserved by other operations), and a draft inventory is created for that
product/location/lot/package, same as with the default strategy.

Resolving the declaration is not done by processing the Loss picking
itself: it is done by processing that inventory, the same way as any other
physical stock count. Applying the counted quantity there automatically
releases the lock and records the correction - with its accounting/
valuation impact - based on the actual count, not on the operator's
on-the-spot report.
