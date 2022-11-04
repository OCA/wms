# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_cluster_picking_base import ClusterPickingLineCommonCase


class ClusterPickingScanLineNoPrefillQtyCase(ClusterPickingLineCommonCase):
    """Tests covering the /scan_line endpoint

    With the no prefill quantity option set

    """

    @classmethod
    def _enable_no_prefill(cls):
        cls.menu.sudo().no_prefill_qty = True
        cls.picking = cls.batch.picking_ids
        cls.line = cls.picking.move_line_ids
        cls.line.product_uom_qty = 3

    def _assert_qty_done(self, line, scanned, expected_qty_done):
        batch = line.picking_id.batch_id
        response = self.service.dispatch(
            "scan_line",
            params={
                "picking_batch_id": batch.id,
                "move_line_id": line.id,
                "barcode": scanned,
            },
        )
        qty_done = response["data"]["scan_destination"]["qty_done"]
        self.assertEqual(qty_done, expected_qty_done)

    def test_scan_line_package_no_prefill_set(self):
        """Check scanning a package when no_prefill_qty is enabled."""
        self._simulate_batch_selected(self.batch, in_package=True)
        self._enable_no_prefill()
        self._assert_qty_done(self.line, self.line.package_id.name, 0.0)

    def test_scan_line_packaging_no_prefill_set(self):
        """Check scanning a packaging when no_prefill_qty is enabled."""
        self._simulate_batch_selected(self.batch, in_package=False)
        self._enable_no_prefill()
        packaging = self.env.ref(
            "stock_storage_type.product_product_9_packaging_4_cardbox"
        )
        packaging.sudo().write(
            {"product_id": self.line.product_id.id, "barcode": "cute-pack"}
        )
        # The quantity of the packaging is incremented
        self._assert_qty_done(self.line, packaging.barcode, packaging.qty)

    def test_scan_line_product_no_prefill_set(self):
        """Check qty done when product is scanned and no_prefill_qty is enabled"""
        self._simulate_batch_selected(self.batch)
        self._enable_no_prefill()
        self._assert_qty_done(self.line, self.line.product_id.barcode, 1.0)

    def test_scan_line_lot_no_prefill_set(self):
        """Check qty done when lot is scanned and no_prefill_qty is enabled"""
        self.product_a.tracking = "lot"
        self._simulate_batch_selected(self.batch, in_lot=True)
        self._enable_no_prefill()
        self._assert_qty_done(self.line, self.line.lot_id.name, 1.0)

    def test_scan_line_location_no_prefill_set(self):
        """Check qty done when location is scanned and no_prefill_qty is enabled"""
        self._simulate_batch_selected(self.batch, in_package=True)
        self._enable_no_prefill()
        self._assert_qty_done(self.line, self.line.location_id.barcode, 0)
