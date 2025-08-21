This module extends the functionality of the [stock_available_to_promise_release](https://github.com/OCA/wms/tree/16.0/stock_available_to_promise_release) module to support automatic unrelease of stock moves when the available quantity changes. It allows users to manage stock moves more efficiently by automatically un-releasing stock moves based on real-time availability, thus improving inventory management and order fulfillment processes.

When a move becomes unavailable, the system will check if the move is the result of a release based on available to promise. If so, it will automatically unrelease the move, ensuring that only available stock is processed in pickings. The unrelease process applies only if:

- The automatic unrelease is enabled for the move's picking type.
- There is no longer enough stock available to promise for the move.
