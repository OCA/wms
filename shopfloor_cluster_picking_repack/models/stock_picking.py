# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_shopfloor_packing_todo = fields.Boolean(
        "Operations need to be packed",
        help="If set, some operations need to be packed by the shopdloor operator",
        compute="_compute_is_shopfloor_packing_todo",
    )

    packing_scanned_packs_str = fields.Char(
        help="Technical field to know which pack has been scanned into the put in "
        "pack process"
    )

    def _get_packages_to_pack(self):
        self.ensure_one()
        return self.mapped("move_line_ids.result_package_id").filtered("is_internal")

    @api.depends("move_line_ids", "move_line_ids.result_package_id")
    def _compute_is_shopfloor_packing_todo(self):
        for rec in self:
            rec.is_shopfloor_packing_todo = False
            for move_line in rec.move_line_ids:
                if (
                    move_line.result_package_id
                    and move_line.result_package_id.is_internal
                ):
                    rec.is_shopfloor_packing_todo = True
                    break

    @property
    def _packing_scanned_packs(self):
        return set(json.loads(self.packing_scanned_packs_str or "[]"))

    def _set_packing_scanned_packs(self, packing_scanned_packs):
        scanned_packs = list(packing_scanned_packs) if packing_scanned_packs else []
        self.packing_scanned_packs_str = json.dumps(scanned_packs)

    def _set_packing_pack_scanned(self, pack_id):
        self.ensure_one()
        self._set_packing_scanned_packs(self._packing_scanned_packs | {pack_id})

    def _is_packing_pack_scanned(self, pack_id):
        self.ensure_one()
        return pack_id in self._packing_scanned_packs

    def _reset_packing_packs_scanned(self):
        for rec in self:
            rec._set_packing_scanned_packs({})

    def is_shopfloor_packing_pack_to_scan(self):
        self.ensure_one()
        return set(self._get_packages_to_pack().ids) != self._packing_scanned_packs
