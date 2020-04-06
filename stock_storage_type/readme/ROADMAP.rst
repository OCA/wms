Currently, the module supports only strategies applied on packages (``stock.quant.package``).
For implementations that do not use packages, it would be possible to add
compatibility with product packaging.

The information needed from a package are:

* the storage type, to know which strategy is applied
* the dimensions and weight, to apply constraints

If we want to support product packaging, we would need to:

* guess the product packaging of a move line based on the product and quantities
  (multiple of a packaging quantity, for instance 8000 would be a pallet if the pallet
  has 2000 units, 1900 would be Box if the Box has 100 units)
* from the product packaging, we know the storage type and dimensions

Everywhere the module is using ``package_id``, we would have to check this:

* use the package if a package is set
* else, use the computed packaging
