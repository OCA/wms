This module adds a "Loss Declaration" strategy to the shopfloor stock issue
mechanism.

Both the default strategy and this one create a draft inventory for someone
to investigate later - a trace exists in both cases. The difference is what
happens immediately, before that investigation takes place: the default
strategy also applies a real inventory correction right away, writing off
the missing quantity from stock (with the corresponding accounting/
valuation impact) based only on what the operator just reported. This
module instead locks the quant through
`stock_picking_operation_loss_quantity`: it gets the same benefit (other
operations are not confronted with the same missing stock) without any
accounting or inventory impact until the inventory created for that quant
is actually processed.

It plugs into the stock issue actions of the Zone Picking, Cluster Picking
and Location Content Transfer scenarios.
