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
