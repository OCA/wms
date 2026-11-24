Currently, the module supports package type from the packages or product. It's
not evaluating the product packaging package type (except for packages where
this can be used for the default package's package type).

If we want to support product packaging, we would need to:

* guess the product packaging of a move line based on the product and quantities
  (multiple of a packaging quantity, for instance 8000 would be a pallet if the pallet
  has 2000 units, 1900 would be Box if the Box has 100 units)
* from the product packaging, we know the storage type and dimensions
