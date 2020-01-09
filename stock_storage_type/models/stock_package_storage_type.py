# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class StockPackageStorageType(models.Model):

    _name = "stock.package.storage.type"
    _description = "Package storage type"

    name = fields.Char(required=True)
    location_storage_type_ids = fields.Many2manyCustom(
        "stock.location.storage.type",
        "stock_location_package_storage_type_rel",
        "package_storage_type_id",
        "location_storage_type_id",
        create_table=False,
        string="Allowed locations storage types",
        help="Locations storage types that can accept such a package storage " "type.",
    )
    product_packaging_ids = fields.One2many(
        "product.packaging", "package_storage_type_id"
    )
