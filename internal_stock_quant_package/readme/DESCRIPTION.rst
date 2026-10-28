This module allows to declare internal stock quant package.

Sometimes, when an operator is picking, he needs to put the product in
internal packages placed on his trolley that will be emptied later.

Two kinds of operations can lead to the emptying of the internal packages:

 * when product from the internal packages will be 'put in pack' at the pack station (in a pick / pack / ship scenario)

 * when a carrier will load his truck with the products from the internal packages (in a pick / ship scenario)

This modules extends the stock module to add the concept of internal stock
quant package and therefore allows you to manage this kind of operational need.
It ensures that the internal stock quant packages are emptied when required
depending on the picking type configuration.
