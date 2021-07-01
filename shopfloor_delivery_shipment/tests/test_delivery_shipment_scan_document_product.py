# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from .test_delivery_shipment_base import DeliveryShipmentCommonCase


class DeliveryShipmentScanDocumentProductCase(DeliveryShipmentCommonCase):
    """Tests for '/scan_document' endpoint when scanning a product."""

    def test_scan_document_product_without_picking(self):
        """Scan a product without having scanned the related operation previously.

        Returns an error telling the user to first scan an operation.
        """
        planned_move = self.picking1.move_lines.filtered(
            lambda m: m.product_id == self.product_c
        )
        self._plan_records_in_shipment(self.shipment, planned_move)
        scanned_product = self.product_d
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": scanned_product.barcode,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            message=self.service.msg_store.scan_operation_first(),
        )

    def test_scan_document_shipment_planned_product_not_planned(self):
        """Scan a product not planned in the shipment advice.

        The shipment advice has some content planned but the user scans an
        unrelated one, returning an error.
        """
        planned_move = self.picking1.move_lines.filtered(
            lambda m: m.product_id == self.product_c
        )
        self._plan_records_in_shipment(self.shipment, planned_move)
        scanned_product = self.product_d
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "picking_id": self.picking1.id,
                "barcode": scanned_product.barcode,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            message=self.service.msg_store.product_not_planned_in_shipment(
                scanned_product, self.shipment
            ),
        )

    def test_scan_document_shipment_planned_product_planned(self):
        """Scan a product planned in the shipment advice.

        The shipment advice has some content planned and the user scans an
        expected one, loading the product and returning the loading list of the
        shipment as it is now fully loaded.
        """
        move_line = self.picking1.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_d
        )
        self._plan_records_in_shipment(self.shipment, move_line.move_id)
        scanned_product = move_line.product_id
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "picking_id": self.picking1.id,
                "barcode": scanned_product.barcode,
            },
        )
        self.assert_response_loading_list(
            response,
            self.shipment,
            message=self.service.msg_store.shipment_planned_content_fully_loaded(),
        )
        # Check product line status
        self.assertEqual(move_line.qty_done, move_line.product_uom_qty)
        # Check returned content
        lading = response["data"]["loading_list"]["lading"]
        on_dock = response["data"]["loading_list"]["on_dock"]
        #   'lading' key contains the related delivery
        self.assertEqual(lading, self.service.data.pickings_loaded(self.picking1))
        #   'on_dock' key is empty as there is no other delivery planned
        self.assertFalse(on_dock)

    def test_scan_document_shipment_not_planned_product_not_planned(self):
        """Scan a product not planned for a shipment not planned.

        Load the product and return the available content to load/unload
        of the related delivery.
        """
        move_line = self.picking1.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_d
        )
        scanned_product = move_line.product_id
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "picking_id": self.picking1.id,
                "barcode": scanned_product.barcode,
            },
        )
        self.assert_response_scan_document(response, self.shipment, self.picking1)
        # Check product line status
        self.assertEqual(move_line.qty_done, move_line.product_uom_qty)
        # Check returned content
        location_src = self.picking_type.default_location_src_id.name
        content = response["data"]["scan_document"]["content"]
        self.assertIn(location_src, content)
        #   'move_lines' key contains the product scanned and other lines not
        # yet loaded from the same delivery
        self.assertEqual(
            content[location_src]["move_lines"],
            self.service.data.move_lines(
                self.picking1.move_ids_without_package.move_line_ids
            ),
        )
        #   'package_levels' key contains the package available from the same delivery
        self.assertEqual(
            content[location_src]["package_levels"],
            self.service.data.package_levels(self.picking1.package_level_ids),
        )

    def test_scan_document_product_already_loaded(self):
        """Scan a product already loaded in the current shipment.

        The second time a product is scanned a warning is returned saying that
        the product has already been loaded.
        """
        move_line = self.picking1.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_d
        )
        scanned_product = move_line.product_id
        # First scan
        self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "picking_id": self.picking1.id,
                "barcode": scanned_product.barcode,
            },
        )
        # Second scan
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "picking_id": self.picking1.id,
                "barcode": scanned_product.barcode,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            self.picking1,
            message=self.service.msg_store.product_already_loaded_in_shipment(
                scanned_product, self.shipment,
            ),
        )
        # Check product line status
        self.assertEqual(move_line.qty_done, move_line.product_uom_qty)
        # Check returned content
        location_src = self.picking_type.default_location_src_id.name
        content = response["data"]["scan_document"]["content"]
        self.assertIn(location_src, content)
        #   'move_lines' key contains the product scanned and other lines not
        # yet loaded from the same delivery
        self.assertEqual(
            content[location_src]["move_lines"],
            self.service.data.move_lines(
                self.picking1.move_ids_without_package.move_line_ids
            ),
        )
        #   'package_levels' key contains the package available from the same delivery
        self.assertEqual(
            content[location_src]["package_levels"],
            self.service.data.package_levels(self.picking1.package_level_ids),
        )

    def test_scan_document_shipment_not_planned_product_planned(self):
        """Scan an already planned product in the shipment not planned.

        Returns an error saying that the product could not be loaded.
        """
        # Grab all lines related to product to plan
        move_lines = self.pickings.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_d
        )
        scanned_product = self.product_d
        # Plan all the product moves in a another shipment
        new_shipment = self._create_shipment()
        self._plan_records_in_shipment(new_shipment, move_lines.move_id)
        # Scan the product: an error is returned as these product lines have
        # already been planned in another shipment
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "picking_id": self.picking1.id,
                "barcode": scanned_product.barcode,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            message=self.service.msg_store.unable_to_load_product_in_shipment(
                scanned_product, self.shipment
            ),
        )

    def test_scan_document_product_owned_by_package(self):
        """Scan a product owned by a package..

        Returns an error telling the user to scan the relevant packages.
        """
        move_line = self.picking1.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_a
        )
        scanned_product = move_line.product_id
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "picking_id": self.picking1.id,
                "barcode": scanned_product.barcode,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            self.picking1,
            message=self.service.msg_store.product_owned_by_packages(
                move_line.package_level_id.package_id
            ),
        )

    def test_scan_document_product_owned_by_lots(self):
        """Scan a product owned by several lots.

        Returns an error telling the user to scan the relevant lots.
        """
        self.pickings.do_unreserve()
        scanned_product = self.product_d
        scanned_product.tracking = "lot"
        move = self.picking1.move_lines.filtered(
            lambda m: m.product_id == scanned_product
        )
        # Put two lots in stock
        lot1 = self.env["stock.production.lot"].create(
            {"product_id": scanned_product.id, "company_id": self.env.company.id}
        )
        lot2 = self.env["stock.production.lot"].create(
            {"product_id": scanned_product.id, "company_id": self.env.company.id}
        )
        self.env["stock.quant"]._update_available_quantity(
            scanned_product, move.location_id, 5, lot_id=lot1
        )
        self.env["stock.quant"]._update_available_quantity(
            scanned_product, move.location_id, 5, lot_id=lot2
        )
        # Reserve them for a delivery and scan the related product
        self.picking1.action_assign()
        move_lines = move.move_line_ids
        self.assertTrue(move_lines.lot_id)
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "picking_id": self.picking1.id,
                "barcode": scanned_product.barcode,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            self.picking1,
            message=self.service.msg_store.product_owned_by_lots(move_lines.lot_id),
        )
