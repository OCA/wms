This module extends package types Odoo feature in order to compute the move line
put-away location. The package type is taken from the moved package when moving
an entire package, otherwise it is taken from the product.

This module allows you to configure on a package type a sequence of locations
to evaluate. When you do that, the standard put-away computation done by odoo
is replaced by the computation of this module respecting the sequence of
locations.

Put-away locations linked to the package type are processed sequentially, if
said location is a child of the move line's destination location (i.e
either the put-away location or the move's destination location) and if the all
the optional conditions are valid.
For each location, their package type strategy is applied as well as the
restrictions defined on the storage category.

Eligible locations are collected based on the put-away strategy:

- For "None", the location is considered as is.
- For "Ordered Children Locations", children locations are sorted by first by
  max height which is a physical constraint to respect, then putaway sequence
  which allow to favor for example some level or corridor, and finally by name.
- For "Chaotic ABC", locations are first sorted by their abc to match the one
  of the product and there is no sorting by name. Note: provided by
  stock_storage_type_putaway_abc module.

Elected locations are filtered according to the capacity configured on the
package type. The location category must have a capacity configured on the
package type (the quantity doesn't matter, you can just put 1).

For packages, their height and weight may also exclude some locations based on
the limits set on the location category.

The locations are also filtered based on their location category "allow new
product" rule. It can be configured as:

- Must be empty
- Allow mixed products
- Restrict to one product
- Restrict to one lot

The location category define a default rule. You can then configure more
advanced rules to apply different rules based on conditions you have defined
(like "Must be empty" for A products, "Restrict to one product" for B products)

If no suitable location is found, the next location in the sequence will be
searched and so on.

Once a location has been computed by this module, the standard put-away
strategy will be applied on top of it. This allows you to compute an area with
this module and then refine a location inside that area with a fixed location
defined as a standard putaway rule.
