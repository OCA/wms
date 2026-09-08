- Enable the loss feature on the warehouse(s) where this strategy will be
  used: *Inventory > Configuration > Warehouses*, warehouse form, "Loss"
  section, "Enable the Loss feature" (provided by
  `stock_picking_operation_loss_quantity`).
- On the Shopfloor menu of a scenario that supports declaring a stock issue
  (Zone Picking, Cluster Picking, Location Content Transfer), open the
  "Stock issue strategy" option and select "Loss Declaration".

If "Loss Declaration" is selected on a menu for a warehouse where the loss
feature above is not enabled, declaring a stock issue will fail.
