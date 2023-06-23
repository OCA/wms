# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from .test_delivery_shipment_base import DeliveryShipmentCommonCase


class DeliveryShipmentScanDocumentLocationCase(DeliveryShipmentCommonCase):
    """Tests for '/scan_document' endpoint when scanning a location to work from."""

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.location = cls.menu.picking_type_ids.default_location_src_id
        cls.sublocation = cls.env.ref("stock.stock_location_14")
        cls.badlocation = cls.env.ref("stock.stock_location_customers")
        # Create a transfer from the sublocation
        cls.pick_subloc = cls._create_picking(
            cls.picking_type,
            lines=[(cls.product_a, 10), (cls.product_b, 5), (cls.product_c, 7)],
        )
        # Clearing stock in parent location insuring goods are taken from sublocation
        cls._update_qty_in_location(cls.location, cls.product_a, 0)
        cls._fill_stock_for_moves(
            cls.pick_subloc.move_lines[0], location=cls.sublocation
        )
        cls._fill_stock_for_moves(
            cls.pick_subloc.move_lines[1], in_package=True, location=cls.sublocation
        )
        cls._fill_stock_for_moves(
            cls.pick_subloc.move_lines[2], in_lot=True, location=cls.sublocation
        )
        cls.pick_subloc.action_assign()
        assert cls.pick_subloc.state == "assigned"

    def test_scan_document_location_ok_to_work_from(self):
        """Scan a location allowed per the menu transfer type."""
        self._plan_records_in_shipment(self.shipment, self.picking1.move_lines)
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": self.sublocation.barcode,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            location=self.sublocation,
        )

    def test_scan_document_location_not_ok_to_work_from(self):
        """Scan a location not allowed per the menus transfer type."""
        self._plan_records_in_shipment(self.shipment, self.picking1.move_lines)
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": self.badlocation.barcode,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            message=self.service.msg_store.location_not_allowed(),
        )

    def test_scan_document_package_after_location(self):
        """Scan a package when filtereing on a location.

        The filtering should stay on the location and not be on the related picking
        """
        self._plan_records_in_shipment(self.shipment, self.pick_subloc.move_lines)
        package_level = self.pick_subloc.package_level_ids
        scanned_package = package_level.package_id
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": scanned_package.name,
                "location_id": self.sublocation.id,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            location=self.sublocation,
        )

    def test_scan_document_lot_after_location(self):
        """Scan a lot when filtereing on a location.

        The filtering should stay on the location and not be on the related picking.
        """
        self._plan_records_in_shipment(self.shipment, self.pick_subloc.move_lines)
        scanned_lot = self.pick_subloc.move_line_ids.lot_id
        response = self.service.dispatch(
            "scan_document",
            params={
                "shipment_advice_id": self.shipment.id,
                "barcode": scanned_lot.name,
                "location_id": self.sublocation.id,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            location=self.sublocation,
        )

    def test_unload_package_keep_location(self):
        """Check the filtered location is kept when unloading a package."""
        package_level = self.pick_subloc.package_level_ids
        # Load the package level at first
        package_level._load_in_shipment(self.shipment)
        # Then unload it
        response = self.service.dispatch(
            "unload_package_level",
            params={
                "shipment_advice_id": self.shipment.id,
                "package_level_id": package_level.id,
                "location_id": self.sublocation.id,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            location=self.sublocation,
        )

    def test_unload_move_line_keep_location(self):
        """Check the filtered location is kept when unloading a move line."""
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
                "location_id": self.sublocation.id,
            },
        )
        self.assert_response_scan_document(
            response,
            self.shipment,
            move_line.picking_id,
            location=self.sublocation,
        )
