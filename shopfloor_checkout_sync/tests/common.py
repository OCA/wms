# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)


class SyncMixin:
    @classmethod
    def _add_pack_move_after_pick_move(cls, pick_move, picking_type):
        move_vals = {
            "name": pick_move.product_id.name,
            "picking_type_id": picking_type.id,
            "product_id": pick_move.product_id.id,
            "product_uom_qty": pick_move.product_uom_qty,
            "product_uom": pick_move.product_uom.id,
            "location_id": picking_type.default_location_src_id.id,
            "location_dest_id": picking_type.default_location_dest_id.id,
            "state": "waiting",
            "procure_method": "make_to_order",
            "move_orig_ids": [(6, 0, pick_move.ids)],
            "group_id": pick_move.group_id.id,
        }
        move_vals.update({})
        return cls.env["stock.move"].create(move_vals)
