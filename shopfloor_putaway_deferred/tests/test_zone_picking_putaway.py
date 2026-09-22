# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.shopfloor.tests.test_zone_picking_base import ZonePickingCommonCase

# pylint: disable=missing-return


class TestZonePickingPutaway(ZonePickingCommonCase):
    """Tests for deferred putaway recomputation on scan_source in zone picking."""

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.picking_type.sudo().allow_to_recompute_putaways = True
        cls.picking_type.sudo().defer_putaway_to_operator = True
        # Route product_d to packing_sublocation_a when arriving at packing_location
        cls.env["stock.putaway.rule"].sudo().create(
            {
                "product_id": cls.product_d.id,
                "location_in_id": cls.packing_location.id,
                "location_out_id": cls.packing_sublocation_a.id,
            }
        )
        # Re-reserve picking3 (product_d in zone_sublocation3) so that
        # its move lines are created with putaway_deferred=True
        cls.picking3.do_unreserve()
        cls.picking3.action_assign()

    def test_scan_source_product_applies_deferred_putaway(self):
        """Scanning a product triggers deferred putaway on the selected line."""
        move_line = self.picking3.move_line_ids[0]
        self.assertTrue(move_line.putaway_deferred)
        initial_dest = move_line.location_dest_id

        response = self.service.dispatch(
            "scan_source",
            params={"barcode": self.product_d.barcode},
        )

        self.assertEqual(response["next_state"], "set_line_destination")
        self.assertFalse(move_line.putaway_deferred)
        self.assertNotEqual(move_line.location_dest_id, initial_dest)
        self.assertEqual(move_line.location_dest_id, self.packing_sublocation_a)
