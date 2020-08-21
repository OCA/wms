Glue module between ``shopfloor`` and ``stock_checkout_sync``.

When an operation type has the flag "Checkout Sync" activated,
the first move line to be scanned directly synchronizes the
destination.

The currently supported scenario that sync the destination locations are:

* Cluster Picking
* Location Content Transfer
* Zone Picking

Support for other scenarios may be added later.
