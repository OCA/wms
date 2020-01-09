# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class StockStorageTypePackageLocationRel(models.Model):

    _name = "stock.location.package.storage.type.rel"
    _description = "Location Package storage type relation"

    package_storage_type_id = fields.Many2one(
        "stock.package.storage.type", required=True
    )
    location_storage_type_id = fields.Many2one(
        "stock.location.storage.type", required=True
    )
