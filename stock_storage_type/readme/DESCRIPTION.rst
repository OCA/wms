This module extends package types Odoo feature in order to better manage stock
moves with packages according to the packaging and stock location properties
(like height, weight or any customized conditions).

Moreover, this module implements "package type put-away strategy" in order to
compute a put-away location using package types.

The standard put-away strategy is applied *before* the package type put-away
strategy as the former relies on product or product category and the latter
relies on stock packages.

In other words, when a move is reserved, Odoo standard put-away strategy will be
applied to compute a new destination on the stock move lines, according to the
product.
After this first "put-away computation", the "package type" put-away strategy
is applied, if the reserved quant is linked to a package defining a package type.

Storage locations linked to the package type are processed sequentially, if
said storage location is a child of the move line's destination location (i.e
either the put-away location or the move's destination location).
For each location, their package type strategy is applied as well as the
restrictions defined on the storage category.
If no suitable location is found, the next location in the sequence will be
searched and so on.

For the package type putaway strategy "None", the location is considered as is.  For
the "ordered children" strategy, children locations are sorted by first by max
height which is a physical constraint to respect, then pack putaway sequence
which allow to favor for example some level or corridor, and finally by name.

At the end, if found location is not the same as the original destination location,
the putaway strategies are applied (e.g.: A "None" pack putaway strategy is set on
computed location and a putaway rule exists on that one).
