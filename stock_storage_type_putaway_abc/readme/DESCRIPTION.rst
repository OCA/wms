This module implements chaotic storage 'ABC' according to Package Storage Type
and Location Storage Type.

The locations and products get an 'a', 'b' or 'c' storage (by default 'b').

For the computation of the putaway, the locations are sorted first by max
height which is a physical constraint to respect, then by 'ABC' as following:

* if the product is 'a', then locations are sorted by 'a', 'b', 'c'
* if the product is 'b', then locations are sorted by 'b', 'c', 'a'
* if the product is 'c', then locations are sorted by 'c', 'b', 'a'

Then by pack putaway sequence (this allow to favor for example some level or
corridor), and finally randomly.

The storage type putaway computation will then apply on the list of locations
the additional restrictions and take the first valid location.
