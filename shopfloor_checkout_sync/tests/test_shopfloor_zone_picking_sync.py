# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.addons.shopfloor.tests.test_zone_picking_base import ZonePickingCommonCase

from .common import SyncMixin


class ZonePickingUnloadSetDestinationSync(ZonePickingCommonCase, SyncMixin):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()

        # moves may be in different pickings, but they all deliver the same
        # pack
        cls.move1 = cls.picking1.move_lines
        cls.move2, cls.move3 = cls.picking2.move_lines
        cls.move4 = cls.picking3.move_lines

        # create the destination moves in the packing zone move[1-4] will go to
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
        cls.pack_move4 = cls._add_pack_move_after_pick_move(
            cls.move4, cls.wh.pack_type_id
        )
        (
            cls.pack_move1 | cls.pack_move2 | cls.pack_move3 | cls.pack_move4
        )._assign_picking()

        # activate synchronization of checkout
        cls.wh.pack_type_id.sudo().checkout_sync = True

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

    def test_unload_set_destination_sync(self):
        self.service.work.current_picking_type = self.picking1.picking_type_id
        # set the destination package
        self.service._set_destination_package(
            self.move1.move_line_ids,
            self.move1.move_line_ids.product_uom_qty,
            self.free_package,
        )
        self.service.dispatch(
            "unload_set_destination",
            params={
                "package_id": self.free_package.id,
                "barcode": self.packing_sublocation.barcode,
                "confirmation": True,
            },
        )
        # check data
        self.assertEqual(self.move1.location_dest_id, self.packing_sublocation)
        self.assertEqual(
            self.move1.move_line_ids.location_dest_id, self.packing_sublocation
        )
        self.assertEqual(self.move2.location_dest_id, self.packing_sublocation)
        self.assertEqual(
            self.move2.move_line_ids.location_dest_id, self.packing_sublocation
        )
        self.assertEqual(self.move3.location_dest_id, self.packing_sublocation)
        self.assertEqual(
            self.move3.move_line_ids.location_dest_id, self.packing_sublocation
        )
        self.assertEqual(
            self.move4.move_line_ids.location_dest_id, self.packing_sublocation
        )
        self.assertEqual(self.move4.location_dest_id, self.packing_sublocation)
