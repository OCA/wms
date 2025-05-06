Go to "Inventory > Settings > Package Types" and
"Inventory > Settings > Storage Categories", to define Package Types and Storage
Categories.

Package Type can be set on Product and Product Packaging.

Storage Category can be added to any stock location and will be computed
automatically as Allowed Storage Category on said stock location's
children location.


- Pack put-away strategy

On stock locations, you can define a "Pack put-away strategy" as "Ordered bins",
so that any move, having this locations as its destination, will be put-away
on a children location, according to the restrictions from package types.

- Put-away sequence

For any package types, you must define a Put-away sequence (i.e. stock
location to search) where such a package is allowed to be put-away. Locations
will be processed sequentially and the first one having an allowed child
location (according to restrictions) will be used to put away.

A good practice here, is to set a location accepting this package type without
any restriction as the last location in the sequence, to act as a fallback
if no other location could be found before.

If a location with a 'none' strategy is set in the sequence and matches with the
move line's destination, it will stop evaluating the next locations in the
sequence.
