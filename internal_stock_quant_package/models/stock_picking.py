# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):

    _inherit = "stock.picking"

    empty_internal_package_on_transfer = fields.Boolean(
        compute="_compute_empty_internal_package_on_transfer",
    )

    @api.depends("picking_type_id.empty_internal_package_on_transfer", "carrier_id")
    def _compute_empty_internal_package_on_transfer(self):
        for record in self:
            carrier = record.carrier_id or record.group_id.carrier_id
            carrier_id = carrier.id
            picking_type_id = record.picking_type_id.id
            value = self.env["stock.picking.type"]._empty_internal_package_on_transfer(
                picking_type_id,
                carrier_id,
            )
            record.empty_internal_package_on_transfer = value

    def action_put_in_pack(self):
        self._move_lines_clear_internal_result_packages()
        return super().action_put_in_pack()

    def button_validate(self):
        self._move_lines_clear_internal_result_packages()
        res = super().button_validate()
        self._empty_transferred_internal_packages()
        return res

    def _empty_transferred_internal_packages(self):
        """
        Remove products from internal quant packages on picking done
        """
        pickings = self.filtered(
            lambda p: p.empty_internal_package_on_transfer and p.state == "done"
        )
        packages = pickings.mapped("move_line_ids.package_id")
        internal_packages = packages.filtered("is_internal")
        if internal_packages:
            internal_packages.unpack()

    def _move_lines_clear_internal_result_packages(self):
        """
        Remove links between move lines and stock quant package to ensure
        that move lines are put into a non internal stock.quant.package
        """
        move_lines = self._get_move_lines_internal_package_used_to_empty()
        move_lines.write({"result_package_id": False})

    def _get_move_lines_internal_package_used_to_empty(self):
        pickings = self.filtered("empty_internal_package_on_transfer")
        return pickings.mapped("move_line_ids").filtered(
            lambda line: line.result_package_id.is_internal
        )
