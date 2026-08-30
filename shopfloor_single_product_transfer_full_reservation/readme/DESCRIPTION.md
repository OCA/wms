This module extends the *Single Product Transfer* shopfloor scenario with support
for the *Full Location Reservation* feature.

When the **Process full location reservation** option is enabled on the shopfloor
menu, the system automatically extends the reservation each time the operator is
assigned a move line to work on. The reservation is expanded to cover all
available quantity sharing the same product, lot, package, and owner at the
source location — not just the quantity originally requested.

This allows operators to clear a source location in a single pass without having
to process the remaining quantity through separate operations.
