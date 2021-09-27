# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from .test_delivery_shipment_base import DeliveryShipmentCommonCase


class DeliveryShipmentScanDocumentPackageCase(DeliveryShipmentCommonCase):
    """Tests for '/scan_document' endpoint when scanning a package."""

    def test_scan_document_shipment_planned_package_not_planned(self):
        """Scan a package not planned in the shipment advice.

        The shipment advice has some content planned but the user scans an
        unrelated one, returning an error.
        """
        self._plan_records_in_shipment(self.shipment, self.picking1.move_lines)
        scanned_package = self.picking2.package_level_ids.package_id
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": scanned_package.name,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            message=self.service.msg_store.package_not_planned_in_shipment(
                scanned_package, self.shipment
            ),
        )

    def test_scan_document_shipment_planned_package_planned(self):
        """Scan a package planned in the shipment advice.

        The shipment advice has some content planned and the user scans an
        expected one, loading the package and returning the loading list of the
        shipment as it is now fully loaded.
        """
        package_level = self.picking1.package_level_ids
        self._plan_records_in_shipment(
            self.shipment, package_level.move_line_ids.move_id
        )
        scanned_package = package_level.package_id
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": scanned_package.name,
            },
        )
        self.assert_response_loading_list(
            response,
            self.shipment,
            message=self.service.msg_store.shipment_planned_content_fully_loaded(),
        )
        # Check package level status
        self.assertTrue(package_level.is_done)
        # Check returned content
        lading = response["data"]["loading_list"]["lading"]
        on_dock = response["data"]["loading_list"]["on_dock"]
        #   'lading' key contains the related delivery
        self.assertEqual(lading, self.service.data.pickings_loaded(self.picking1))
        #   'on_dock' key is empty as there is no other delivery planned
        self.assertFalse(on_dock)

    def test_scan_document_shipment_not_planned_package_not_planned(self):
        """Scan a package not planned for a shipment not planned.

        Load the package and return the available content to load/unload
        of the related delivery.
        """
        package_level = self.picking1.package_level_ids
        scanned_package = package_level.package_id
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": scanned_package.name,
            },
        )
        self.assert_response_scan_document(response, self.shipment, self.picking1)
        # Check package level status
        self.assertTrue(package_level.is_done)
        # Check returned content
        location_src = self.picking_type.default_location_src_id.name
        content = response["data"]["scan_document"]["content"]
        self.assertIn(location_src, content)
        #   'move_lines' key contains the lines available from the same delivery
        self.assertEqual(
            content[location_src]["move_lines"],
            self.service.data.move_lines(self.picking1.move_line_ids_without_package),
        )
        #   'package_levels' key contains the package which has been loaded
        self.assertEqual(
            content[location_src]["package_levels"],
            self.service.data.package_levels(package_level),
        )

    def test_scan_document_package_already_loaded(self):
        """Scan a package already loaded in the current shipment.

        The second time a package is scanned an warning is returned saying that
        the package has already been loaded.
        """
        package_level = self.picking1.package_level_ids
        scanned_package = package_level.package_id
        # First scan
        self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": scanned_package.name,
            },
        )
        # Second scan
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": scanned_package.name,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            self.picking1,
            message=self.service.msg_store.package_already_loaded_in_shipment(
                scanned_package,
                self.shipment,
            ),
        )
        # Check package level status
        self.assertTrue(package_level.is_done)
        # Check returned content
        location_src = self.picking_type.default_location_src_id.name
        content = response["data"]["scan_document"]["content"]
        self.assertIn(location_src, content)
        #   'move_lines' key contains the only one product without package
        self.assertEqual(
            content[location_src]["move_lines"],
            self.service.data.move_lines(self.picking1.move_line_ids_without_package),
        )
        #   'package_levels' key contains the package which has been loaded
        self.assertEqual(
            content[location_src]["package_levels"],
            self.service.data.package_levels(package_level),
        )

    def test_scan_document_shipment_not_planned_package_planned(self):
        """Scan an already planned package in the shipment not planned.

        Returns an error saying that the package could not be loaded.
        """
        package_level = self.picking1.package_level_ids
        scanned_package = package_level.package_id
        # Plan the package in a another shipment
        new_shipment = self._create_shipment()
        self._plan_records_in_shipment(
            new_shipment, package_level.move_line_ids.move_id
        )
        # Scan the package: an error is returned as this package has already
        # been planned in another shipment
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": scanned_package.name,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            message=self.service.msg_store.unable_to_load_package_in_shipment(
                scanned_package, self.shipment
            ),
        )
