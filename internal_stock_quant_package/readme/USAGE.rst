As this addon rely on the concept of "internal" packages. If you want to
use packages into your picking operations, you need first to activate the
package functionality in the stock settings (see the "Operations" section).

Then, you need to create packages and set them as internal. This is done
by going to Inventory > Products > Packages and clicking on the "Create".
(Don't forget to tick the "Internal use" box).

By default, when you put your products into an internal package when processing
a picking, once the picking is done, the package is automatically emptied.
You can change this behavior at 2 levels:

1. At the picking type level: go to "Inventory > Configuration > Operation
Types" and edit the picking type you want to change. Then, untick the "Empty
Internal Package On Transfer" box. (By default internal packages are always
emptied when the picking is done).
2. At the picking type level for a specific carrier: go to "Inventory >
Configuration > Operation Types" and edit the picking type you want to change.
Then, add or remove lines in the "Stock Internal Package Config Line" table.
You can add a line for a specific carrier and tick/untick the "Empty" box.

To know if internal packages must be emptied or not for a given picking, the
system will first check if a configuration line exists on the picking type for
the carrier of the picking. If a line exists, the system will use the value
of the "Empty" box. If no line exists, the system will use the value of the
"Empty Internal Package On Transfer" box of the picking type.
