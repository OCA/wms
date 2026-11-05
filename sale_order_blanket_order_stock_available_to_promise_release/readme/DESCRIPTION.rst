This module extends ``sale_stock_available_to_promise_release`` to show stock
availability on blanket order lines, based on active prebook reservations and
the remaining call-off quantity, expressed in the line's unit of measure.

The call-off creation wizard displays availability and allows filtering lines
by status. The filter is informational and does not limit requested quantities.

Blanket orders reserving stock at call-off have no prebook moves before call-off
creation and therefore show no available quantity, even if physical stock exists.
