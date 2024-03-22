Based on *stock_service_level* module, this allows to restrict and configure
routes per `stock.service.level`.

Using *sale_stock_service_level* user is able to set the stock service level
(offer / service) on sale order.

This information will be propagated over procurement on stock move line.

Two stock move lines with different stock service level won't be merged
which allow to change product route according restrictions configured on
stock routes.

For instance this let you sale same product with standard level and premium
level. The premium service is allowed to use stock while the standard would
generate a purchase order to the supplier leading to extra times before
deliveries.

