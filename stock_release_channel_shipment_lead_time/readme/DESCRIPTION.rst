Manage shipment date and delivery lead time on release channel.
The shipment date is computed automatically base on process end date + shipment
lead time days and warehouse calendar.

Exclude deliveries promised after shipment date. A delivery with a deadline
won't be assigned to a channel with a shipment date prior to the deadline. This
allows to prevent to deliver a sales order with a commitment date in the
future.

Adapt computation of release ready to take into account the shipment lead time.
A delivery part of a release channel won't be counted as release ready if the
scheduled date is after the shipment date.

Add the delivery date on the shipment advice.
