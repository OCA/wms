This module introduces two new models in order to manage stock moves with
 packages according to the packaging and stock location properties.

* Stock package storage type (`stock.package.storage.type`)

  This model is linked to product.packaging and defines the type of storage
  related to a specific packaging.

* Stock location storage type (`stock.location.storage.type`)

  This models is linked to stock.location and defines the types of storage
  that are allowed for a specific location.

Therefore a Stock location storage type can include different Stock package
storage type in order to validate the destination of a move with package into a
stock location.
Moreover Stock location storage type can include product, size or lot
restrictions for the stock locations it's defined on, so that a move with
package will only be allowed if it doesn't violate the restrictions defined
(cf stock_location_storage_type_strategy).

Moreover, this module implements "storage type put-away strategy" in order to compute a
put-away location using storage types.

The standard put-away strategy is applied *before* the storage type put-away
strategy as the former relies on product or product category and the latter
relies on stock packages.

In other words, when a move is assigned, Odoo standard put-away strategy will be
applied to compute a new destination on the stock move lines, according to the
product.
After this first "put-away computation", the "storage type" put-away strategy
is applied, if the reserved quant is linked to a package defining a package
storage type.

Storage locations linked to the package storage are processed sequentially, if
said storage location is a child of the move line's destination location (i.e
either the put-away location or the move's destination location), then it will
be searched in order to find a children location that is allowed according to
the restrictions defined on the stock location storage types.
If no suitable location is found, the next location in the sequence will be
searched and so on.
