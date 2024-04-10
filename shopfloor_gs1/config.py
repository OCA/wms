# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# https://www.gs1.org/standards/barcodes/application-identifiers
# TODO: define other internal mappings by convention


# Each type can be mapped to multiple AIs.
# For instance, you can search a product by barcode (01) or manufacturer code (240).
MAPPING_TYPE_TO_AI = {
    "product": ("01", "240"),
    "lot": ("10",),
    "production_date": ("11",),
    "serial": ("21",),
    "manuf_product_code": ("240",),
    "location": ("254",),
}
MAPPING_AI_TO_TYPE = {
    "01": "product",
    "10": "lot",
    "11": "production_date",
    "21": "serial",
    "240": "product",
    "254": "location",
}
