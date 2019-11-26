- Pack storage strategy

On stock locations, you can define a "Pack storage strategy" as "Ordered bins",
so that any move, having this locations as its destination, will be put-away
on a child location, according to the restrictions from storage types.

- Storage locations

On stock package storage type, you can define Storage locations where such
a package is allowed to be put-away. Locations will be processed sequentially
and the first one having an allowed child location (according to restrictions)
will be used to putaway.
