# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.shopfloor.tests.test_location_content_transfer_base import (
    LocationContentTransferCommonCase,
)

# pylint: disable=missing-return


class TestLocationContentTransferGetWork(LocationContentTransferCommonCase):
    """
    Tests for putaways recomputations
    """

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.menu.sudo().allow_get_work = True
        cls.pickings = cls.env["stock.picking"].search(
            [("location_id", "=", cls.stock_location.id)]
        )
        cls.move_lines = cls.pickings.move_line_ids.filtered(
            lambda line: line.qty_done == 0
            and line.state in ("assigned", "partially_available")
            and not line.shopfloor_user_id
        )
        products = cls.product_a + cls.product_b + cls.product_c + cls.product_d
        for product in products:
            cls.env["stock.putaway.rule"].sudo().create(
                {
                    "product_id": product.id,
                    "location_in_id": cls.stock_location.id,
                    "location_out_id": cls.shelf1.id,
                }
            )

        cls.picking1 = picking1 = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls.picking2 = picking2 = cls._create_picking(
            lines=[(cls.product_c, 10), (cls.product_d, 10)]
        )
        cls.pickings = picking1 | picking2
        cls.content_loc2 = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Content Location 2",
                    "barcode": "Content2",
                    "location_id": cls.picking_type.default_location_src_id.id,
                }
            )
        )
        cls._fill_stock_for_moves(
            picking1.move_ids, in_package=True, location=cls.content_loc
        )
        cls._fill_stock_for_moves(picking2.move_ids[0], location=cls.content_loc2)
        cls._fill_stock_for_moves(picking2.move_ids[1], location=cls.content_loc)
        cls.pickings.action_assign()

        cls.picking_type.sudo().allow_to_recompute_putaways = True

    def _get_location_lines(self, location):
        return self.env["stock.move.line"].search([("location_id", "=", location.id)])

    def test_find_work_work_with_package(self):
        """ """
        next_location = self.service._find_location_to_work_from()
        self.assertEqual(self.picking1.move_line_ids[0].location_dest_id, self.shelf1)
        rule = self.env["stock.putaway.rule"].search(
            [("product_id", "=", self.product_a.id)]
        )
        rule.sudo().location_out_id = self.shelf2
        response = self.service.dispatch("find_work", params={})
        self.assert_response(
            response,
            next_state="scan_location",
            data={
                "location": self.data.location(next_location),
            },
        )
        self.assertEqual(self.picking1.move_line_ids[0].location_dest_id, self.shelf1)
        lines = self._get_location_lines(next_location)
        self.assertEqual(lines.shopfloor_user_id, self.env.user)
        # Confirm the location
        response = self.service.dispatch(
            "scan_location", params={"barcode": next_location.name}
        )
        self.assertEqual(response["next_state"], "scan_destination_all")

    def test_find_work_work_without_package(self):
        """ """
        next_location = self.service._find_location_to_work_from()
        self.assertEqual(self.picking1.move_line_ids[0].location_dest_id, self.shelf1)
        rule = self.env["stock.putaway.rule"].search(
            [("product_id", "=", self.product_a.id)]
        )
        rule.sudo().location_out_id = self.shelf2
        self.picking1.move_line_ids.result_package_id = False
        response = self.service.dispatch("find_work", params={})
        self.assert_response(
            response,
            next_state="scan_location",
            data={
                "location": self.data.location(next_location),
            },
        )
        self.assertEqual(self.picking1.move_line_ids[0].location_dest_id, self.shelf2)

        # this to ensure we retrieve that line as service result
        self.picking1.move_line_ids[0].shopfloor_priority = 1

        lines = self._get_location_lines(next_location)
        self.assertEqual(lines.shopfloor_user_id, self.env.user)
        # Confirm the location
        response = self.service.dispatch(
            "scan_location", params={"barcode": next_location.name}
        )

        self.assertEqual(
            response.get("data")
            .get("start_single")
            .get("move_line")
            .get("location_dest")
            .get("id"),
            self.shelf2.id,
        )
