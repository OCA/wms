In supply chain and retail operations, GTIN-13 (EAN-13) barcodes are frequently encoded in physical 14-digit GTIN formats (such as GS1 DataMatrix or ITF-14) by adding a leading zero (`0`). 

When users scan these physical 14-digit barcodes, native Odoo barcode lookup mechanisms fail if the product or package record in the database is stored using the standard 13-digit GTIN/EAN format.
