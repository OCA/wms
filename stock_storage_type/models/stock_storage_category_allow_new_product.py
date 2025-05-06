# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class StockStorageCategoryAllowNewProduct(models.Model):
    _name = "stock.storage.category.allow_new_product"
    _description = "Storage Category Allow New Product Rule"
    _order = "storage_category_id, sequence"

    def _selection_allow_new_product(self):
        return self.env["stock.storage.category"]._fields["allow_new_product"].selection

    storage_category_id = fields.Many2one(
        comodel_name="stock.storage.category",
        ondelete="cascade",
        required=True,
        index=True,
    )
    condition_ids = fields.Many2many(
        comodel_name="stock.storage.category.allow_new_product.cond",
        relation="stock_storage_category_allow_new_product_cond_rel",
        string="Conditions",
        required=True,
        help="All conditions have to match to apply the Allow New Product policy.",
    )
    allow_new_product = fields.Selection(
        selection=_selection_allow_new_product, default="mixed", required=True
    )
    sequence = fields.Integer(index=True)
