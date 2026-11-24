When the operator starts an operation, if putaway strategies have not yet been
applied (deferred mode), the destination location could be wrong.

So, when launching 'Get Work', we need to apply the deferred putaways for the
selected move lines. The `stock_picking_putaway_deferred` module provides the
mechanism to defer putaway calculation until this moment.
