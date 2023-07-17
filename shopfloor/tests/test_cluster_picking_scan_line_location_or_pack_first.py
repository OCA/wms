# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_cluster_picking_base import ClusterPickingLineCommonCase

# pylint: disable=missing-return


class ClusterPickingScanLineLocationOrPackFirstCase(ClusterPickingLineCommonCase):
    """Tests covering the /scan_line endpoint

    When the scan location or pack frist option enabled.

    """

    def setUp(self):
        super().setUp()
        self.menu.sudo().scan_location_or_pack_first = True

    def _scan_line_error(self, line, scanned, message, sublocation=None):
        batch = line.picking_id.batch_id
        response = self.service.dispatch(
            "scan_line",
            params={
                "picking_batch_id": batch.id,
                "move_line_id": line.id,
                "barcode": scanned,
                "sublocation_id": sublocation.id if sublocation else None,
            },
        )
        kw = {"sublocation": self.data.location(sublocation)} if sublocation else {}
        self.assert_response(
            response,
            next_state="start_line",
            data=self._line_data(line, scan_location_or_pack_first=True, **kw),
            message=message,
        )
        return response

    def _scan_line_ok(self, line, scanned, expected_qty_done=1, sublocation_id=None):
        batch = line.picking_id.batch_id
        response = self.service.dispatch(
            "scan_line",
            params={
                "picking_batch_id": batch.id,
                "move_line_id": line.id,
                "barcode": scanned,
                "sublocation_id": sublocation_id,
            },
        )
        self.assert_response(
            response,
            next_state="scan_destination",
            data=self._line_data(
                line, qty_done=expected_qty_done, scan_location_or_pack_first=True
            ),
        )

    def test_scan_line_product_ask_for_package(self):
        """Check scanning the product first will request to scan the package.

        This is if the line being worked on as a package.

        """
        self._simulate_batch_selected(self.batch, in_package=True, in_lot=False)
        line = self.batch.picking_ids.move_line_ids
        location = self.batch.picking_ids.location_id
        self._update_qty_in_location(location, self.product_a, 2)
        self._scan_line_error(
            line,
            line.product_id.barcode,
            self.msg_store.line_has_package_scan_package(),
        )

    def test_scan_line_product_ask_for_location(self):
        """Check scanning the product first will request to scan the location.

        That is if the product on the move line is tracked by lot.

        """
        self._simulate_batch_selected(self.batch, in_package=False, in_lot=True)
        line = self.batch.picking_ids.move_line_ids
        location = self.batch.picking_ids.location_id
        self._update_qty_in_location(location, self.product_a, 2)
        self._scan_line_error(
            line, line.product_id.barcode, self.msg_store.scan_the_location_first()
        )

    def test_scan_line_location_ask_for_package(self):
        """Check scanning location for a line with pack will ask to scan the pack."""
        self._simulate_batch_selected(self.batch, in_package=True, in_lot=False)
        line = self.batch.picking_ids.move_line_ids
        location = self.batch.picking_ids.location_id
        self._update_qty_in_location(location, self.product_a, 2)
        self._scan_line_error(
            line,
            line.location_id.barcode,
            self.msg_store.line_has_package_scan_package(),
            sublocation=location,
        )

    def test_scan_line_location_with_multiple_product(self):
        """Check scanning a location then a product without package.

        When there is multiple product in the location and the location is scanned,
        The user needs to scan the product but the system does not remember the location ?

        """
        self._simulate_batch_selected(self.batch, in_package=False, in_lot=False)
        line = self.batch.picking_ids.move_line_ids
        location = self.batch.picking_ids.location_id
        self._update_qty_in_location(location, self.product_a, 2)
        self._update_qty_in_location(location, self.product_b, 2)
        self._scan_line_ok(line, line.product_id.barcode, 1.0, location.id)
