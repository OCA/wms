# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from .test_delivery_shipment_base import DeliveryShipmentCommonCase


class DeliveryShipmentScanDocumentPickingCase(DeliveryShipmentCommonCase):
    """Tests for '/scan_document' endpoint when scanning a delivery."""

    def test_scan_document_barcode_not_found(self):
        response = self.service.dispatch(
            "scan_document",
            params={"shipment_advice_id": self.shipment.id, "barcode": "UNKNOWN"},
        )
        self.assert_response_scan_document(
            response, self.shipment, message=self.service.msg_store.barcode_not_found(),
        )

    def test_scan_document_shipment_planned_picking_not_planned(self):
        """Scan a delivery not planned in the shipment advice.

        The shipment advice has some deliveries planned but the user scans an
        unrelated one, returning an error.
        """
        self._plan_records_in_shipment(self.shipment, self.picking1 | self.picking2)
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": self.picking3.name,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            message=self.service.msg_store.picking_not_planned_in_shipment(
                self.picking3, self.shipment
            ),
        )

    def test_scan_document_shipment_planned_picking_planned(self):
        """Scan a delivery planned in the shipment advice.

        The shipment advice has some deliveries planned and the user scans an
        expected one, returning the planned content of this delivery for the
        current shipment.
        """
        self._plan_records_in_shipment(self.shipment, self.picking1)
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": self.picking1.name,
            },
        )
        self.assert_response_scan_document(
            response, self.shipment, self.picking1,
        )
        # Check returned content
        location_src = self.picking_type.default_location_src_id.name
        content = response["data"]["scan_document"]["content"]
        self.assertIn(location_src, content)
        #   'move_lines' key contains the only one product without package
        self.assertEqual(
            content[location_src]["move_lines"],
            self.service.data.move_lines(self.picking1.move_line_ids_without_package),
        )
        #   'package_levels' key contains the packages
        self.assertEqual(
            content[location_src]["package_levels"],
            self.service.data.package_levels(self.picking1.package_level_ids),
        )

    def test_scan_document_shipment_planned_picking_partially_planned(self):
        """Scan a delivery partially planned in the shipment advice.

        The shipment advice has some deliveries planned and the user scans an
        expected one, returning the planned content of this delivery for the
        current shipment.
        """
        self._plan_records_in_shipment(
            self.shipment, self.picking1.move_ids_without_package
        )
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": self.picking1.name,
            },
        )
        self.assert_response_scan_document(
            response, self.shipment, self.picking1,
        )
        # Check returned content
        location_src = self.picking_type.default_location_src_id.name
        content = response["data"]["scan_document"]["content"]
        self.assertIn(location_src, content)
        #   'move_lines' key contains the only one product without package
        self.assertEqual(
            content[location_src]["move_lines"],
            self.service.data.move_lines(self.picking1.move_line_ids_without_package),
        )
        #   'package_levels' key doesn't exist (not planned for this shipment)
        self.assertNotIn("package_levels", content[location_src])

    def test_scan_document_shipment_not_planned_picking_carrier_unrelated(self):
        """Scan a delivery whose the carrier doesn't belong to the related
        carriers of the shipment (if any).

        This is only relevant for shipment without planned content.
        """
        self.picking1.carrier_id = self.env.ref("delivery.delivery_carrier")
        self.picking1.carrier_id.sudo().delivery_type = "base_on_rule"
        self.picking2.carrier_id = self.env.ref("delivery.normal_delivery_carrier")
        self.picking2.carrier_id.sudo().delivery_type = "fixed"
        # Load the first delivery in the shipment
        self.picking1._load_in_shipment(self.shipment)
        # Scan the second which has a different carrier => error
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": self.picking2.name,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            message=self.service.msg_store.carrier_not_allowed_by_shipment(
                self.picking2
            ),
        )

    def test_scan_document_shipment_not_planned_picking_not_planned(self):
        """Scan a delivery without content planned for a shipment not planned.

        Returns the full content of the scanned delivery.
        """
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": self.picking1.name,
            },
        )
        self.assert_response_scan_document(response, self.shipment, self.picking1)

    def test_scan_document_shipment_not_planned_picking_fully_planned(self):
        """Scan an already fully planned delivery for a shipment not planned.

        Returns an error saying that the delivery can not be loaded.
        """
        # Plan the whole delivery in a another shipment
        new_shipment = self._create_shipment()
        self._plan_records_in_shipment(new_shipment, self.picking1)
        # Scan the delivery: get an error
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": self.picking1.name,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            message=self.service.msg_store.no_delivery_content_to_load(self.picking1),
        )

    def test_scan_document_shipment_not_planned_picking_partially_planned(self):
        """Scan a delivery with some content planned for a shipment not planned.

        Returns the not planned content of the scanned delivery.
        """
        # Plan the move without package in a another shipment
        new_shipment = self._create_shipment()
        self._plan_records_in_shipment(
            new_shipment, self.picking1.move_ids_without_package
        )
        # Scan the delivery: only the not planned content is returned (i.e. the
        # remaining package here).
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": self.picking1.name,
            },
        )
        self.assert_response_scan_document(response, self.shipment, self.picking1)
        # Check returned content
        location_src = self.picking_type.default_location_src_id.name
        content = response["data"]["scan_document"]["content"]
        #   'move_lines' key doesn't exist (planned in another shipment)
        self.assertNotIn("move_lines", content[location_src])
        #   'package_levels' key contains the not planned packages
        self.assertEqual(
            content[location_src]["package_levels"],
            self.service.data.package_levels(self.picking1.package_level_ids),
        )

    def test_scan_document_shipment_not_planned_picking_without_content_to_load(self):
        """Scan a delivery without content to load for a shipment not planned.

        Returns an error.
        """
        # Load the whole delivery in a another shipment
        new_shipment = self._create_shipment()
        self.picking1._load_in_shipment(new_shipment)
        # Scan the delivery: an error is returned as no more content can be
        # loaded from this delivery
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": self.picking1.name,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            message=self.service.msg_store.no_delivery_content_to_load(self.picking1),
        )

    def test_scan_document_shipment_not_planned_picking_partially_loaded(self):
        """Scan a delivery with content partially loaded in a shipment not planned.

        Returns the content which is:
            - not planned
            - not loaded (in any shipment)
            - already loaded in the current shipment
        """
        # Load the move without package in a another shipment
        new_shipment = self._create_shipment()
        self.picking1.move_ids_without_package.move_line_ids._load_in_shipment(
            new_shipment
        )
        # Load the package level in the current shipment
        self.picking1.package_level_ids._load_in_shipment(self.shipment)
        # Scan the delivery: returns the already loaded package levels as content
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": self.picking1.name,
            },
        )
        self.assert_response_scan_document(
            response, self.shipment, self.picking1,
        )
        # Check returned content
        location_src = self.picking_type.default_location_src_id.name
        content = response["data"]["scan_document"]["content"]
        #   'move_lines' key doesn't exist (loaded in another shipment)
        self.assertNotIn("move_lines", content[location_src])
        #   'package_levels' key contains the already loaded package levels
        self.assertEqual(
            content[location_src]["package_levels"],
            self.service.data.package_levels(self.picking1.package_level_ids),
        )
