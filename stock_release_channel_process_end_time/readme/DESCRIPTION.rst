This module allows to configure an end time on a release channel that will become the channel end date when the channel awakes. This process end date specify when all the work in the channel should be finalized.
Note: ensure to configure the timezone on the address of the warehouse to have the right time to datetime conversion.

The channel process end date can be propagated to the generated pickings in order to solve two challenges:

- You expect to view the stock pickings in the same order as the the one you
  have set as process end date on the release channel. This way you can easily
  manage the deliveries in the same order as the one expected by the planned
  release channels.

- You expect to set as deadline of your released move operations the process
  end date of the release channel. This is useful to ensure that move created
  when releasing deliveries get the same deadline as the one set on the
  release channel. This is also required to allow the merge of move operations
  generated for the same product, location in the same stock picking.

