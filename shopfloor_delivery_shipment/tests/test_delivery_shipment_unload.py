# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from .test_delivery_shipment_base import DeliveryShipmentCommonCase


class DeliveryShipmentUnloadCase(DeliveryShipmentCommonCase):
    """Tests for the following endpoints:

    - /unload_move_line
    - /unload_package_level
    """

    def test_unload_move_line_wrong_id(self):
        """Try to unload a move line which doesn't exist (wrong ID)."""
        response = self.service.dispatch(
            "unload_move_line",
            params={
                "shipment_advice_id": self.shipment.id,
                "move_line_id": -1,  # Wrong ID
            },
        )
        self.assert_response_scan_dock(
            response,
            message=self.service.msg_store.record_not_found(),
        )

    def test_unload_move_line_ok(self):
        """Unload a move line and returns the content of the related delivery."""
        move_line = self.picking1.move_lines.filtered(
            lambda m: m.product_id == self.product_c
        ).move_line_ids
        # Load the move line at first
        move_line._load_in_shipment(self.shipment)
        # Then unload it
        response = self.service.dispatch(
            "unload_move_line",
            params={
                "shipment_advice_id": self.shipment.id,
                "move_line_id": move_line.id,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            move_line.picking_id,
        )

    def test_unload_package_level_wrong_id(self):
        """Try to unload a package level which doesn't exist (wrong ID)."""
        response = self.service.dispatch(
            "unload_package_level",
            params={
                "shipment_advice_id": self.shipment.id,
                "package_level_id": -1,  # Wrong ID
            },
        )
        self.assert_response_scan_dock(
            response,
            message=self.service.msg_store.record_not_found(),
        )

    def test_unload_package_level_ok(self):
        """Unload a package level and returns the content of the related delivery."""
        package_level = self.picking1.package_level_ids
        # Load the package level at first
        package_level._load_in_shipment(self.shipment)
        # Then unload it
        response = self.service.dispatch(
            "unload_package_level",
            params={
                "shipment_advice_id": self.shipment.id,
                "package_level_id": package_level.id,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            package_level.picking_id,
        )
