# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.shopfloor.tests.test_zone_picking_base import ZonePickingCommonCase


class TestZonePickingForcePackage(ZonePickingCommonCase):
    def setUp(self):
        super().setUp()
        self.service.work.current_picking_type = self.picking1.picking_type_id

    def test_set_destination_location_package_restriction(self):
        """Check error restriction on location is properly forwarded to frontend."""
        # Add a restriction on the location
        self.packing_location.sudo().package_restriction = "singlepackage"
        # Add a first package on the location
        self.pack_1 = self.env["stock.quant.package"].create(
            {"location_id": self.packing_location.id}
        )
        self._update_qty_in_location(
            self.packing_location, self.product_a, 1, package=self.pack_1
        )
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_lines.move_line_ids
        move_line.qty_done = move_line.product_uom_qty
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.packing_location.barcode,
                "quantity": move_line.product_uom_qty,
                "confirmation": False,
            },
        )
        message = {
            "message_type": "error",
            "body": (
                f"Only one package is allowed on the location "
                f"{self.packing_location.display_name}.You cannot add "
                f"the {move_line.package_id.name}, there is already {self.pack_1.name}."
            ),
        }
        self.assert_response_set_line_destination(
            response,
            self.zone_location,
            picking_type,
            move_line,
            message=message,
            qty_done=10.0,
        )
