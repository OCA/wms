# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestSetQuantityCheckoutSync(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.location = cls.location_src
        cls.product = cls.product_a

    @classmethod
    def _setup_picking(cls):
        cls._add_stock_to_product(cls.product, cls.location, 10)
        return cls._create_picking(lines=[(cls.product, 10)])

    @classmethod
    def _setup_chained_picking(cls, picking):
        next_moves = picking.move_lines.browse()
        for move in picking.move_lines:
            next_moves |= move.copy(
                {
                    "move_orig_ids": [(6, 0, move.ids)],
                    "location_id": move.location_dest_id.id,
                    "location_dest_id": cls.customer_location.id,
                }
            )
        next_moves._assign_picking()
        next_picking = next_moves.picking_id
        next_picking.action_confirm()
        next_picking.action_assign()
        return next_picking

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
        return cls.env["stock.move"].create(move_vals)

    def test_set_quantity_child_move_location(self):
        if "checkout_sync" not in self.env["stock.picking.type"]._fields:
            # checkout_sync module not installed nothing to test
            return
        picking1 = self._setup_picking()
        picking2 = self._setup_picking()
        move1 = picking1.move_lines
        move2 = picking2.move_lines
        pack_move1 = self._add_pack_move_after_pick_move(move1, self.wh.pack_type_id)
        pack_move2 = self._add_pack_move_after_pick_move(move2, self.wh.pack_type_id)
        (pack_move1 | pack_move2)._assign_picking()
        # Activating the checkout sync on transfer type
        self.wh.sudo().pack_type_id.checkout_sync = True
        self.service.dispatch(
            "scan_product",
            params={"location_id": self.location.id, "barcode": self.product.barcode},
        )
        move_line = picking1.move_line_ids
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.qty_done,
                "barcode": self.dispatch_location.name,
            },
        )
        expected_message = self.msg_store.transfer_done_success(move_line.picking_id)
        data = {"location": self._data_for_location(self.location)}
        completion_info = self.service._actions_for("completion.info")
        expected_popup = completion_info.popup(move_line)
        self.assert_response(
            response,
            next_state="select_product",
            message=expected_message,
            data=data,
            popup=expected_popup,
        )
        self.assertEqual(move1.move_line_ids.location_dest_id, self.dispatch_location)
        # Move synchronize for checkout
        self.assertEqual(move2.location_dest_id, self.dispatch_location)
