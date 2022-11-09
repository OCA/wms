# Copyright 2022 ACSONE SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class StockStorageCategory(models.Model):

    _inherit = "stock.storage.category"

    allow_new_product = fields.Selection(
        selection_add=[("same_lot", "If lots are all the same")],
        ondelete={"same_lot": "cascade"},
    )

    computed_location_ids = fields.One2many(
        comodel_name="stock.location", inverse_name="computed_storage_category_id"
    )

    # TODO: Move these fields in another module ?
    max_height = fields.Float(
        string="Max height (mm)",
        help="The max height supported for this storage category.",
    )

    max_height_in_m = fields.Float(
        help="Technical field, to speed up comparaisons",
        compute="_compute_max_height_in_m",
        store=True,
    )
    weight_uom_id = fields.Many2one(
        # Same as product.packing
        "uom.uom",
        string="Weight Units of Measure",
        domain=lambda self: [
            ("category_id", "=", self.env.ref("uom.product_uom_categ_kgm").id)
        ],
        help="Weight Unit of Measure",
        compute=False,
        default=lambda self: self.env[
            "product.template"
        ]._get_weight_uom_id_from_ir_config_parameter(),
    )
    weight_uom_name = fields.Char(
        # Same as product.packing
        string="Weight unit of measure label",
        related="weight_uom_id.name",
        readonly=True,
    )
    max_weight_in_kg = fields.Float(
        help="Technical field, to speed up comparaisons",
        compute="_compute_max_weight_in_kg",
        store=True,
    )

    length_uom_id = fields.Many2one(
        # Same as product.packing
        "uom.uom",
        "Dimensions Units of Measure",
        domain=lambda self: [
            ("category_id", "=", self.env.ref("uom.uom_categ_length").id)
        ],
        help="UoM for height",
        default=lambda self: self.env[
            "product.template"
        ]._get_length_uom_id_from_ir_config_parameter(),
    )

    _sql_constraints = [
        (
            "positive_max_height",
            "CHECK(max_height >= 0)",
            "Max height should be a positive number.",
        ),
    ]

    @api.depends("max_height", "length_uom_id")
    def _compute_max_height_in_m(self):
        uom_m = self.env.ref("uom.product_uom_meter")
        for slst in self:
            slst.max_height_in_m = slst.length_uom_id._compute_quantity(
                qty=slst.max_height,
                to_unit=uom_m,
                round=False,
            )

    @api.depends("max_weight")
    def _compute_max_weight_in_kg(self):
        uom_kg = self.env.ref("uom.product_uom_kgm")
        for slst in self:
            slst.max_weight_in_kg = slst.weight_uom_id._compute_quantity(
                qty=slst.max_weight,
                to_unit=uom_kg,
                round=False,
            )
