# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.shopfloor_base.utils import ensure_model


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @property
    def _package_parser(self):
        res = super()._package_parser
        res.append("is_internal")
        return res

    def _data_for_packing_info(self, picking):
        """Return the packing information

        Intended to be extended.
        """
        # TODO: This could be avoided if included in the picking parser.
        return ""

    def select_package(self, picking, lines):
        return {
            "selected_move_lines": self.move_lines(lines.sorted()),
            "picking": self.picking(picking),
            "packing_info": self._data_for_packing_info(picking),
            # "no_package_enabled": (
            #     not self.options.get("checkout__disable_no_package"),
            # )
            # Used by inheriting module
            "package_allowed": True,
        }

    @ensure_model("stock.picking")
    def pack_picking(self, record, **kw):
        return {
            "id": record.id,
            "name": record.name,
            "partner": {"id": record.partner_id.id, "name": record.partner_id.name},
            "scanned_packs": list(record._packing_scanned_packs),
            "move_lines": [
                self._pack_picking_move_lines(ml) for ml in record.move_line_ids
            ],
        }

    def _pack_picking_move_lines(self, record):
        return {
            "id": record.id,
            "qty_done": record.qty_picked,
            "product": self.product(
                record.product_id or record.package_id.single_product_id
            ),
            "package_src": self.package(record.package_id, record.picking_id),
            "package_dest": self.package(
                record.result_package_id.with_context(
                    picking_id=record.picking_id.id, no_quantity=True
                ),
                record.picking_id,
            ),
        }
