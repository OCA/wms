Extension for Shopfloor's cluster picking.

When a user uses the "Get Work" button on the barcode device, if no transfer
batch is available, it automatically creates a new batch for the user.

Some options can be configured on the Shopfloor menu:

* Activate or not the batch creation
* Group by commercial entity
* Max number of transfer per batch
* Max weight per batch
* Max volume per batch

The rules are:

* Transfers of higher priority are put first in the batch
* If some transfers are assigned to the user, the batch will only contain
  those, otherwise, it looks for unassigned transfers
* Priorities are not mixed to make transfers with higher priority faster
  e.g. if the limit is 5, with 3 Very Urgent transfer and 10 Normal transfer,
  the batch will contain only the 3 Very Urgent despite the higher limit
* The weight and volume are based on the Product Packaging when their weight and
  volume are defined
