# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.shopfloor.tests.test_cluster_picking_unload import (
    ClusterPickingUnloadingCommonCase,
)


class TestShopfloorLocationSuggestion(ClusterPickingUnloadingCommonCase):
    def test_location_suggestion(self):
        """All move lines have different destination locations"""
        move_lines = self.move_lines
        self._set_dest_package_and_done(move_lines[:2], self.bin1)
        self._set_dest_package_and_done(move_lines[2:], self.bin2)
        move_lines[:2].write({"location_dest_id": self.packing_a_location.id})
        move_lines[2:].write({"location_dest_id": self.packing_b_location.id})
        response = self.service.dispatch(
            "prepare_unload", params={"picking_batch_id": self.batch.id}
        )
        first_line = move_lines[0]
        location = first_line.location_dest_id
        data = self._data_for_batch(self.batch, location, pack=self.bin1)
        self.assert_response(
            response,
            next_state="unload_single",
            data=data,
        )

        # Create a second batch
        self.batch = self._create_picking_batch(
            [
                [
                    self.BatchProduct(product=self.product_a, quantity=10),
                    self.BatchProduct(product=self.product_b, quantity=10),
                ],
                [self.BatchProduct(product=self.product_a, quantity=10)],
            ]
        )
        self._simulate_batch_selected(self.batch)

        second_move_lines = self.batch.picking_ids.move_line_ids

        self.bin3 = self.env["stock.quant.package"].create({})

        self._set_dest_package_and_done(second_move_lines[0], self.bin3)

        response = self.service.dispatch(
            "prepare_unload", params={"picking_batch_id": self.batch.id}
        )

        location = first_line.location_dest_id
        data = self._data_for_batch(self.batch, location, pack=self.bin1)
        self.assert_response(
            response,
            next_state="unload_single",
            data=data,
        )
