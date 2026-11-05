This module acts as an integration layer between `stock_available_to_promise_release`
and `stock_restrict_lot`, enabling advanced stock allocation based on both
available-to-promise quantities and lot restrictions.

By combining available-to-promise logic with lot restriction functionality, 
this module enhances stock move allocation by:
- Allowing stock moves to respect both priority and specific lot allocations.
- Ensuring that available quantities are promised according to move priority, but only when the lot matches the restriction.
