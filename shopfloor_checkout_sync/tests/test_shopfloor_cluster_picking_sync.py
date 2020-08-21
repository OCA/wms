# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.addons.shopfloor.tests.test_cluster_picking_unload import (
    ClusterPickingUnloadingCommonCase,
)

from .common import SyncMixin


class TestShopfloorCheckoutSync(ClusterPickingUnloadingCommonCase, SyncMixin):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()

        # moves may be in different pickings, but they all deliver the same
        # pack
        cls.move1, cls.move2, cls.move3 = cls.batch.mapped("picking_ids.move_lines")
        # create the destination moves in the packing zone
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
        # activate synchronization of checkout
        cls.wh.pack_type_id.sudo().checkout_sync = True

    def test_unload_scan_destination_sync_checkout(self):
        """When a destination is set, it applies the sync"""
        self._set_dest_package_and_done(self.move1.move_line_ids, self.bin1)
        self.service.dispatch(
            "unload_scan_destination",
            params={
                "picking_batch_id": self.batch.id,
                "package_id": self.bin1.id,
                "barcode": self.packing_a_location.barcode,
            },
        )

        # the scanned location has been synchronized to all the other moves
        # and lines that reach the same packing destination
        self.assertEqual(self.move1.location_dest_id, self.packing_a_location)
        self.assertEqual(
            self.move1.move_line_ids.location_dest_id, self.packing_a_location
        )

        self.assertEqual(self.move2.location_dest_id, self.packing_a_location)
        self.assertEqual(
            self.move2.move_line_ids.location_dest_id, self.packing_a_location
        )

        self.assertEqual(self.move3.location_dest_id, self.packing_a_location)
        self.assertEqual(
            self.move3.move_line_ids.location_dest_id, self.packing_a_location
        )
