The *Single Product Transfer* scenario is designed for picking operations where
operators process one product at a time: they scan a source location or package,
scan a product, enter the quantity, and confirm the destination. By default, the
move lines are limited to exactly the quantities already reserved in the stock
operations.

In some warehouse workflows — such as quality control restocking, inventory
consolidation, or location clearance — operators must move the entire available
quantity of a product from a source location in one go, even when the original
picking only reserved part of it. The `stock_full_location_reservation` module
provides the underlying mechanism to extend a stock reservation to the full
available content of a location.

The `shopfloor_full_location_reservation` module exposes that mechanism as a
per-menu option (*Process full location reservation*) for shopfloor scenarios.
However, because the *Single Product Transfer* scenario works line by line and
filters by product/lot/package/owner, a plain full-location reservation (which
would capture every product in the location) is too coarse.

This module bridges the gap: it hooks into `_get_next_move_line_to_work` and,
when the option is active, triggers a **strict** full location reservation scoped
to the exact product, lot, package, and owner of the assigned move line. 
