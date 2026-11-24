When both `stock_available_to_promise_release` and `stock_restrict_lot` modules
are installed, the calculation of quantities available to promise doesn't 
properly account for lot restrictions. This results in a priority conflict, 
where higher-priority moves that are restricted to a specific lot receive 
available quantities from any lot, bypassing their lot restriction.

The issue manifests as follows:
- A move with a higher priority, restricted to a specific lot, is promised the available quantity regardless of lot constraints.
- If the restricted lot is allocated to another move with lower priority, the lower-priority move can not be promised its designated lot.

In effect, lot-restricted moves cannot accurately reserve quantities based on 
both priority and specific lot requirements.
This can lead to stock release issues, where low-priority moves fail to secure
stock from their restricted lots due to incorrect available to promise calculations in higher-priority moves.