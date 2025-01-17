Currently, the module supports only strategies applied on packages
(`stock.quant.package`). For implementations that do not use packages,
it would be possible to add compatibility with product packaging.

The information needed from a package are:

- the storage type, to know which strategy is applied
- the dimensions and weight, to apply constraints

If we want to support product packaging, we would need to:

- guess the product packaging of a move line based on the product and
  quantities (multiple of a packaging quantity, for instance 8000 would
  be a pallet if the pallet has 2000 units, 1900 would be Box if the Box
  has 100 units)
- from the product packaging, we know the storage type and dimensions

Everywhere the module is using `package_id`, we would have to check
this:

- use the package if a package is set
- else, use the computed packaging

About Unit of Measures:

In v13, there is an assumption of height to be expressed in mm and
weight in kg. In v14, packaging can be expressed in differents units.
Explicit fields are introduced like max_weight_in_kg in order make
simple and efficient computations.

## Limitation

If the locations structure is using views intensively in order to
separate storage types kindly (not mixing them), Odoo standard method to
get putaway strategy is returning the first child if a move location
destination is a view.

This is not convenient if we want to set specific strategies on that
view. So, we override standard process by returning the view itself (if
no putaway is set).

This can lead to a change on standard behavior as people will need to
change manually the location destination for pickings with views as
default destination.

Idea: maybe adding a field on view locations to say 'this is a view but
don't apply standard child location selection' could help filtering view
candidates.
