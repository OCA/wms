Go to Inventory > Configuration > Delivery > Preferred Shipping Methods to
define new Preferred Shipping Methods.

A Preferred Shipping Method can either define a specific Delivery Method or
use the partner's defined Delivery Method.

These Preferred Shipping Methods will then be filtered out according to the
picking's estimated shipping weight.

Estimated shipping weight calculation relies on `product_total_weight_from_packaging`,
i.e. packaging weight if defined, with a fallback on product weight and uses
the quantity available to promise only.
