**Source location selection**
  Select a source location.
  It must be a valid location according to the configuration of the scenario,
  and there must be stock in the selected location.

**Move line selection**
  Select a product or a lot in this location.
  If an unassigned move line for this product / lot exists in the previously selected
  location, then it is selected.
  Otherwise, if the `Allow Move Creation` is enabled, it will try to create a move line.
  If the `Allow to process reserved quantities` option is enabled, other moves
  will be unreserved.
  If there's unreserved goods in the location, a new move is created with quantity equal
  to the unreserved goods in the location.

**Set quantity / destination location**
  1. **Scan a product / lot to set the quantity**
     If the `Do not pre-fill quantity to pick` option is enabled, it will increment the
     done quantity by 1 each time the product or lot barcode is scanned.
     Else, it will set the quantity done as the reserved quantity.
  2. **Scan a destination location**
     The scanned location will be checked.
     It must be a child of the current line destination location or a child of
     the scenario default destination location.
     If this is ok, then the move is processed.
