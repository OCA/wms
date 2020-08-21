# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.addons.shopfloor.tests.test_location_content_transfer_base import (
    LocationContentTransferCommonCase,
)

from .common import SyncMixin


class ZonePickingUnloadSetDestinationSync(LocationContentTransferCommonCase, SyncMixin):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.picking_type.sudo().default_location_dest_id = cls.packing_location
        cls.picking = picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10), (cls.product_c, 10)]
        )

        cls.move1, cls.move2, cls.move3 = picking.move_lines
        # create the destination moves in the packing zone move[1-3] will go to
        # the same pack picking, so their destination location must be sync'ed
        # in the same packing location as soon as the first move line is done
        cls.pack_move1 = cls._add_pack_move_after_pick_move(
            cls.move1, cls.wh.pack_type_id
        )
        cls.pack_move2 = cls._add_pack_move_after_pick_move(
            cls.move2, cls.wh.pack_type_id
        )
        cls.pack_move3 = cls._add_pack_move_after_pick_move(
            cls.move3, cls.wh.pack_type_id
        )
        (cls.pack_move1 | cls.pack_move2 | cls.pack_move3)._assign_picking()

        cls._fill_stock_for_moves(cls.move1, in_package=True, location=cls.content_loc)
        picking.action_assign()
        cls._simulate_pickings_selected(picking)

        cls.packing_sublocation = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Packing sublocation",
                    "location_id": cls.packing_location.id,
                    "barcode": "PACKING_SUBLOCATION",
                }
            )
        )
        # activate synchronization of checkout
        cls.wh.pack_type_id.sudo().checkout_sync = True

    def test_set_destination_package_dest_location_ok_sync(self):
        """Sync destination of other lines when dest. is set on 1st line"""
        package_level = self.picking.package_level_ids[0]
        self.service.dispatch(
            "set_destination_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
                "barcode": self.packing_sublocation.barcode,
            },
        )

        self.assertEqual(self.move1.location_dest_id, self.packing_sublocation)
        self.assertEqual(
            self.move1.move_line_ids.location_dest_id, self.packing_sublocation
        )
        # no move line yet for move2 and 3
        self.assertEqual(self.move2.location_dest_id, self.packing_sublocation)
        self.assertEqual(self.move3.location_dest_id, self.packing_sublocation)

        # add stock for move2 and 3
        self._fill_stock_for_moves(
            self.move2, in_package=True, location=self.content_loc
        )
        self._fill_stock_for_moves(
            self.move3, in_package=True, location=self.content_loc
        )
        (self.move2 | self.move3)._action_assign()

        self.assertEqual(
            self.move2.move_line_ids.location_dest_id, self.packing_sublocation
        )
        self.assertEqual(
            self.move2.move_line_ids.package_level_id.location_dest_id,
            self.packing_sublocation,
        )
        self.assertEqual(
            self.move3.move_line_ids.location_dest_id, self.packing_sublocation
        )
        self.assertEqual(
            self.move3.move_line_ids.package_level_id.location_dest_id,
            self.packing_sublocation,
        )
