This module implements "storage type strategy" in order to compute a putaway
location using storage types (cf `stock_storage_type`).

The storage type strategy is applied *after* the putaway strategy.

In other words, when a move is assigned, Odoo standard putaway strategy will be
applied to compute a new destination on the stock move lines, according to the
product.
After this "putaway computation", the "storage type" strategy is applied, if
the reserved quant is linked to a package defining a package storage type.

Storage locations linked to the package storage are processed sequentially, if
said storage location is a child of the move line's destination location (i.e
either the putaway location or the move's destination location), in order to
find a location that is allowed according to the restrictions defined on stock
location storage type.
