# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.shopfloor.tests.test_location_content_transfer_base import (
    LocationContentTransferCommonCase,
)
from odoo.addons.shopfloor_base.tests.common import CommonCase


# pylint: disable=missing-return
class TestShopfloorScenario(CommonCase):
    @classmethod
    def setUpClassUsers(cls):
        super().setUpClassUsers()
        cls.env = cls.env(user=cls.shopfloor_manager)

    def test_scenario(self):
        scenario = self.env.ref("shopfloor.scenario_location_content_transfer")
        self.assertTrue(scenario.options["full_location_reservation"])


class LocationContentTransferFull(LocationContentTransferCommonCase):
    """
        Tests for Stock Content Transfer in Full Reservation context

    * /set_destination_line

    """

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 5.0)]
        )
        cls.picking.picking_type_id.sudo().merge_move_for_full_location_reservation = (
            True
        )
        defaults = {
            "location_id": cls.picking.location_id.id,
            "name": "Sub location 1",
            "barcode": "SUBLOCATION1",
        }
        cls.sub_location_1 = cls.picking.location_id.sudo().copy(defaults)
        defaults = {
            "location_id": cls.picking.location_id.id,
            "name": "Sub location 2",
            "barcode": "SUBLOCATION2",
        }
        cls.sub_location_2 = cls.picking.location_id.sudo().copy(defaults)
        defaults = {
            "location_id": cls.picking.location_id.id,
            "name": "Sub location 3",
            "barcode": "SUBLOCATION3",
        }
        cls.sub_location_3 = cls.picking.location_id.sudo().copy(defaults)

        cls._update_qty_in_location(cls.sub_location_1, cls.product_a, 5)
        # Set more quantities on sub location 2 to trigger a move creation
        cls._update_qty_in_location(cls.sub_location_2, cls.product_a, 10)
        cls._update_qty_in_location(cls.sub_location_3, cls.product_b, 5)
        # Reserve quantities
        cls.picking.action_assign()
        # cls._simulate_pickings_selected(cls.picking)
        cls.dest_location = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Sub Shelf 1",
                    "barcode": "subshelf1",
                    "location_id": cls.shelf1.id,
                }
            )
        )

    def test_scan_location_assignation(self):
        """
        Test case:

            - Product A is present in several sub location of 'Stock':
                - Sub location 1 : 5.0
                - Sub location 2 : 10.0
            - Product B is present in sub location 3 (5.0)

        When scanning the location origin for product A (in sub location 1),
        the
        """
        self.menu.sudo().full_location_reservation = True
        self.service.dispatch("scan_location", params={"barcode": "SUBLOCATION1"})
        move_a_after = self.env["stock.move"].search(
            [
                ("product_id", "=", self.product_a.id),
                ("state", "=", "assigned"),
                ("picking_id", "!=", self.picking.id),
            ]
        )

        self.assertEqual("assigned", self.picking.state)

        # Check the move have been changed to a new picking
        move_a = self.picking.move_ids.filtered(
            lambda move: move.product_id == self.product_a
        )
        self.assertNotEqual(move_a, move_a_after)

        self.assertEqual(1, len(move_a_after.move_line_ids))

        self.assertEqual(5.0, move_a.product_uom_qty)
        self.assertEqual(5.0, move_a_after.product_uom_qty)
