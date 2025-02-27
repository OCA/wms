By default Odoo takes the Shipping Policy set in the procurement group,
or fallbacks on the one configured on the Operation Type.

This module adds a Force Shipping Policy field on Operations Types to ensure
transfers will take the policy according to their types, ignoring the one set
on the Procurement Group.

This is especially useful if you use a pick-pack-ship setup with the
release of operation (`stock_available_to_promise_release`) module along
side with the `stock_dynamic_routing` that may split operations by zone
of the warehouse. In that case, you want to be sure the pack operations
will wait all different picks to be processed before releasing the
availability of the pack operation.
