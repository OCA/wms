# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools


class StockPickingType(models.Model):

    _inherit = "stock.picking.type"

    empty_internal_package_on_transfer = fields.Boolean(
        help="If set internal packages are emptied after the transfer or "
        "when products are put in pack.",
        default=True,
    )
    stock_internal_package_config_line_ids = fields.One2many(
        comodel_name="stock.internal.package.config.line",
        inverse_name="stock_picking_type_id",
    )

    @api.model
    @tools.ormcache("picking_type_id", "carrier_id")
    def _empty_internal_package_on_transfer(self, picking_type_id, carrier_id):
        """
        To know if internal packages must be emptied:
        1. We check if the flag is set on the picking type
        2. We lookup if a specific configuration exists for the given partner
        3. If a specific configuration exists we return the value of this configuration
        4. Otherwise we return the value on the picking type.
        """
        picking_type = self.browse(picking_type_id)
        result = picking_type.empty_internal_package_on_transfer
        lines = picking_type.stock_internal_package_config_line_ids
        carrier_line = lines.filtered(
            lambda cl: cl.delivery_carrier_id.id == carrier_id
        )
        if carrier_line:
            result = carrier_line.empty
        return result
