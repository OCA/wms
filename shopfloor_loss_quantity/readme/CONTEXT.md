Both the default stock issue handling and the strategy added by this module
create a draft inventory for someone to check later - a trace always
exists. The difference is what happens immediately, before anyone actually
investigates: by default, an inventory correction is applied right away, so
the missing quantity is written off the stock accounts based solely on the
operator's on-the-spot report, with the corresponding accounting/valuation
impact.

In warehouses where a loss must be confirmed by an actual investigation
before it is allowed to impact stock valuation, this is undesirable. This
module reuses the loss declaration mechanism of
`stock_picking_operation_loss_quantity` instead: the quant is only locked
(blocked from being reserved by other operations), with no accounting or
inventory impact, until the inventory created for that quant is actually
processed - at which point the lock is released automatically and the
correction, based on the real count, is applied.
