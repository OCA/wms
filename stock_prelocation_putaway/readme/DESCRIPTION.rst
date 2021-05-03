This module allows to use pre-sort locations.

For instance, in a warehouse with alleys named A,B,C and D:
- WH/STOCK/A
- WH/STOCK/B
- WH/STOCK/C
- WH/STOCK/D

You want to sort goods in the INPUT zone (2 step reception) according to the alleys. Let's says there is 2 sublocations in input:
- INPUT/AB (for alleys A and B)
- INPUT/CD (for alleys C and D)

And there is some putaway rules:
- Product_1, WH/STOCK -> WH/STOCK/A
- Product_2, WH/STOCK -> WH/STOCK/D

During a reception, the location_dest of move lines in the first picking
will be pre-filled with pre-locations.

Picking 1 (from Suppliers to WH/INPUT)
Product_1 from Suppliers to WH/INPUT/AB
Product_2 from Supplires to WH/INPUT/CD

Picking 2 (from WH/INPUT to WH/STOCK)
Product_1 from WH/INPUT/AB to WH/STOCK/A
Product_2 from WH/INPUT/CD to WH/STOCK/D
