# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from .test_delivery_shipment_base import DeliveryShipmentCommonCase


class DeliveryShipmentValidateCase(DeliveryShipmentCommonCase):
    """Tests for '/validate' endpoint."""

    def test_validate_wrong_id(self):
        response = self.service.dispatch("validate", params={"shipment_advice_id": -1})
        self.assert_response_scan_dock(
            response, message=self.service.msg_store.record_not_found()
        )

    def test_validate_shipment_planned_partially_loaded(self):
        """Validate a planned shipment with part of it loaded."""
        # Plan 3 deliveries in the shipment
        self._plan_records_in_shipment(self.shipment, self.pickings.move_lines)
        self.shipment.action_confirm()
        self.shipment.action_in_progress()
        # Load a part of it
        #   - part of picking1
        move_line_d = self.picking1.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_d
        )
        move_line_d._load_in_shipment(self.shipment)
        #   - all content of picking2
        self.picking2._load_in_shipment(self.shipment)
        #   - nothing from picking3
        # Get the summary
        response = self.service.dispatch(
            "validate", params={"shipment_advice_id": self.shipment.id}
        )
        self.assert_response_validate(response, self.shipment)
        # Check returned content
        lading = response["data"]["validate"]["lading"]
        on_dock = response["data"]["validate"]["on_dock"]
        #   'lading' key contains loaded goods
        self.assertEqual(lading["loaded_pickings_count"], 2)
        self.assertEqual(lading["loaded_packages_count"], 1)
        self.assertEqual(lading["loaded_bulk_lines_count"], 3)
        self.assertEqual(lading["total_packages_count"], 2)
        self.assertEqual(lading["total_bulk_lines_count"], 4)
        #   'on_dock' key contains picking3
        self.assertEqual(on_dock["total_pickings_count"], 1)
        self.assertEqual(on_dock["total_packages_count"], 1)
        self.assertEqual(on_dock["total_bulk_lines_count"], 2)
        # Validate the shipment
        response = self.service.dispatch(
            "validate",
            params={"shipment_advice_id": self.shipment.id, "confirmation": True},
        )
        self.assert_response_scan_dock(
            response,
            message=self.service.msg_store.shipment_validated(self.shipment),
        )
        # Check data
        self.assertEqual(self.picking1.state, self.picking2.state, "done")
        self.assertEqual(self.picking3.state, "assigned")
        self.assertTrue(self.picking1.backorder_ids)
        self.assertFalse(self.picking2.backorder_ids)

    def test_validate_shipment_planned_fully_loaded(self):
        """Validate a planned shipment fully loaded."""
        # Plan 3 deliveries in the shipment
        self._plan_records_in_shipment(self.shipment, self.pickings.move_lines)
        self.shipment.action_confirm()
        self.shipment.action_in_progress()
        # Load everything
        self.pickings._load_in_shipment(self.shipment)
        # Get the summary
        response = self.service.dispatch(
            "validate", params={"shipment_advice_id": self.shipment.id}
        )
        self.assert_response_validate(response, self.shipment)
        # Check returned content
        lading = response["data"]["validate"]["lading"]
        on_dock = response["data"]["validate"]["on_dock"]
        #   'lading' key contains loaded goods
        self.assertEqual(lading["loaded_pickings_count"], 3)
        self.assertEqual(lading["loaded_packages_count"], 3)
        self.assertEqual(lading["total_packages_count"], 3)
        self.assertEqual(lading["loaded_bulk_lines_count"], 6)
        self.assertEqual(lading["total_bulk_lines_count"], 6)
        #   'on_dock' key is empty as everything has been loaded
        self.assertEqual(on_dock["total_pickings_count"], 0)
        self.assertEqual(on_dock["total_packages_count"], 0)
        self.assertEqual(on_dock["total_bulk_lines_count"], 0)
        # Validate the shipment
        response = self.service.dispatch(
            "validate",
            params={"shipment_advice_id": self.shipment.id, "confirmation": True},
        )
        self.assert_response_scan_dock(
            response,
            message=self.service.msg_store.shipment_validated(self.shipment),
        )
        # Check data
        self.assertTrue(all([s == "done" for s in self.pickings.mapped("state")]))
        self.assertFalse(self.picking1.backorder_ids)
        self.assertFalse(self.picking2.backorder_ids)

    def test_validate_shipment_not_planned_loaded(self):
        """Validate a unplanned shipment with some content loaded."""
        self.shipment.action_confirm()
        self.shipment.action_in_progress()
        # Load some content
        #   - part of picking1
        move_line_d = self.picking1.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_d
        )
        move_line_d._load_in_shipment(self.shipment)
        #   - all content of picking2
        self.picking2._load_in_shipment(self.shipment)
        #   - nothing from picking3
        # Get the summary
        response = self.service.dispatch(
            "validate", params={"shipment_advice_id": self.shipment.id}
        )
        self.assert_response_validate(response, self.shipment)
        # Check returned content
        lading = response["data"]["validate"]["lading"]
        on_dock = response["data"]["validate"]["on_dock"]
        #   'lading' key contains loaded goods
        self.assertEqual(lading["loaded_pickings_count"], 2)
        self.assertEqual(lading["loaded_packages_count"], 1)
        self.assertEqual(lading["total_packages_count"], 2)
        self.assertEqual(lading["loaded_bulk_lines_count"], 3)
        self.assertEqual(lading["total_bulk_lines_count"], 4)
        #   'on_dock' key contains picking3 (at least, as there is others
        # existing deliveries in the demo data)
        self.assertTrue(on_dock["total_pickings_count"] >= 1)
        self.assertTrue(on_dock["total_packages_count"] >= 1)
        self.assertTrue(on_dock["total_bulk_lines_count"] >= 2)
        # Validate the shipment
        response = self.service.dispatch(
            "validate",
            params={"shipment_advice_id": self.shipment.id, "confirmation": True},
        )
        self.assert_response_scan_dock(
            response,
            message=self.service.msg_store.shipment_validated(self.shipment),
        )
        # Check data
        self.assertEqual(self.picking1.state, self.picking2.state, "done")
        self.assertEqual(self.picking3.state, "assigned")
        self.assertTrue(self.picking1.backorder_ids)
        self.assertFalse(self.picking2.backorder_ids)
