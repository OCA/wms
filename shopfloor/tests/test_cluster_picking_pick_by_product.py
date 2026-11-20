# Copyright 2026  Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .test_cluster_picking_base import ClusterPickingCommonCase


class ClusterPickingProductScanCase(ClusterPickingCommonCase):
    """Tests for the 'Product scan pick all goods' menu option.

    When enabled, scanning a product (no source package, not tracked by
    lot/serial) shows a summary screen and allows batch-processing all
    lines of that product at once.
    """

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.batch = cls._create_picking_batch(
            [
                [cls.BatchProduct(product=cls.product_a, quantity=10)],
                [cls.BatchProduct(product=cls.product_a, quantity=20)],
                [cls.BatchProduct(product=cls.product_b, quantity=10)],
                [cls.BatchProduct(product=cls.product_a, quantity=5)],
            ]
        )
        cls.menu.sudo().write({"pick_by_product": True})
        cls._simulate_batch_selected(cls.batch)

    def test_confirm_start_goes_to_start_product_when_aggregatable_lines_exist(self):
        """After confirming a batch with aggregatable lines, go to start_product."""
        response = self.service.dispatch(
            "confirm_start",
            params={"picking_batch_id": self.batch.id},
        )
        # First product by picking sequence should be product_a
        self.assertEqual(response["next_state"], "start_product")
        data = response["data"]["start_product"]
        self.assertEqual(data["product"]["id"], self.product_a.id)
        self.assertEqual(data["quantity"], 35.0)
        self.assertEqual(len(data["lines"]), 3)

    def test_confirm_start_goes_to_start_line_when_no_aggregatable_lines(self):
        """Without aggregatable lines, start_line is shown directly."""
        self.menu.sudo().write({"pick_by_product": False})
        batch = self._create_picking_batch(
            [[self.BatchProduct(product=self.product_a, quantity=10)]]
        )
        self._simulate_batch_selected(batch)
        response = self.service.dispatch(
            "confirm_start",
            params={"picking_batch_id": batch.id},
        )
        self.assertEqual(response["next_state"], "start_line")

    def test_scan_product_correct_barcode(self):
        """Scanning the expected product barcode goes to scan_product_destination."""
        self.service.dispatch(
            "confirm_start",
            params={"picking_batch_id": self.batch.id},
        )
        response = self.service.dispatch(
            "scan_product",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.product_a.barcode,
            },
        )
        self.assertEqual(response["next_state"], "scan_product_destination")
        data = response["data"]["scan_product_destination"]
        self.assertEqual(data["product"]["id"], self.product_a.id)
        self.assertEqual(data["quantity"], 35.0)
        self.assertEqual(len(data["lines"]), 3)

    def test_scan_product_wrong_barcode(self):
        """Scanning the wrong barcode stays in start_product with an error."""
        self.service.dispatch(
            "confirm_start",
            params={"picking_batch_id": self.batch.id},
        )
        response = self.service.dispatch(
            "scan_product",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": "WRONG_BARCODE",
            },
        )
        self.assertEqual(response["next_state"], "start_product")

    def test_scan_product_wrong_product_barcode(self):
        """Scanning a barcode of another product stays in start_product."""
        self.service.dispatch(
            "confirm_start",
            params={"picking_batch_id": self.batch.id},
        )
        response = self.service.dispatch(
            "scan_product",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.product_b.barcode,
            },
        )
        self.assertEqual(response["next_state"], "start_product")

    def test_scan_product_destination_pack_single_product(self):
        """Scan destination pack processes all lines of a product."""
        self.service.dispatch(
            "confirm_start",
            params={"picking_batch_id": self.batch.id},
        )
        self.service.dispatch(
            "scan_product",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.product_a.barcode,
            },
        )
        bin1 = self.env["stock.quant.package"].create({})
        response = self.service.dispatch(
            "scan_product_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "product_id": self.product_a.id,
                "location_id": self.stock_location.id,
                "barcode": bin1.name,
                "quantity": 35.0,
            },
        )

        # All product_a lines should have qty_done and result_package_id
        product_a_lines = self.batch.picking_ids.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        for line in product_a_lines:
            self.assertEqual(line.result_package_id, bin1)
        self.assertEqual(sum(product_a_lines.mapped("qty_done")), 35.0)

        # Next state should be start_product for product_b
        self.assertEqual(response["next_state"], "start_product")

    def test_scan_product_destination_pack_full_qty(self):
        """Full quantity is distributed across lines, earliest date first."""
        self.service.dispatch(
            "confirm_start",
            params={"picking_batch_id": self.batch.id},
        )
        self.service.dispatch(
            "scan_product",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.product_a.barcode,
            },
        )
        bin1 = self.env["stock.quant.package"].create({})
        self.service.dispatch(
            "scan_product_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "product_id": self.product_a.id,
                "location_id": self.stock_location.id,
                "barcode": bin1.name,
                "quantity": 35.0,
            },
        )

        # All product_a lines should have full qty done
        product_a_lines = self.batch.picking_ids.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        ).sorted(
            key=lambda l: (
                l.move_id.date,
                l.move_id.sequence,
                l.move_id.id,
                l.id,
            )
        )
        self.assertEqual(product_a_lines[0].qty_done, 10.0)
        self.assertEqual(product_a_lines[1].qty_done, 20.0)
        self.assertEqual(product_a_lines[2].qty_done, 5.0)

    def test_scan_product_destination_pack_partial_qty(self):
        """Partial quantity fills first lines fully, last line gets remainder."""
        self.service.dispatch(
            "confirm_start",
            params={"picking_batch_id": self.batch.id},
        )
        self.service.dispatch(
            "scan_product",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.product_a.barcode,
            },
        )
        bin1 = self.env["stock.quant.package"].create({})
        self.service.dispatch(
            "scan_product_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "product_id": self.product_a.id,
                "location_id": self.stock_location.id,
                "barcode": bin1.name,
                "quantity": 25.0,
            },
        )

        product_a_lines = self.batch.picking_ids.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        ).sorted(
            key=lambda l: (
                l.move_id.date,
                l.move_id.sequence,
                l.move_id.id,
                l.id,
            )
        )
        # First line gets full 10, second gets 15 (remaining), third gets 0
        self.assertEqual(product_a_lines[0].qty_done, 10.0)
        self.assertEqual(product_a_lines[1].qty_done, 15.0)
        self.assertEqual(product_a_lines[2].qty_done, 0)

    def test_after_all_products_goes_to_unload_all(self):
        """After all aggregatable products are done, go to unload_all."""
        self.service.dispatch(
            "confirm_start",
            params={"picking_batch_id": self.batch.id},
        )
        # Process product_a
        self.service.dispatch(
            "scan_product",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.product_a.barcode,
            },
        )
        bin1 = self.env["stock.quant.package"].create({})
        self.service.dispatch(
            "scan_product_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "product_id": self.product_a.id,
                "location_id": self.stock_location.id,
                "barcode": bin1.name,
                "quantity": 35.0,
            },
        )

        # Now process product_b
        self.service.dispatch(
            "scan_product",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.product_b.barcode,
            },
        )
        bin2 = self.env["stock.quant.package"].create({})
        response = self.service.dispatch(
            "scan_product_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "product_id": self.product_b.id,
                "location_id": self.stock_location.id,
                "barcode": bin2.name,
                "quantity": 10.0,
            },
        )

        # All aggregatable products done -> prepare_unload
        # All lines have a destination package -> unload
        self.assertEqual(response["next_state"], "unload_all")

    def test_lot_tracked_line_not_aggregated(self):
        """A lot-tracked line is not aggregated."""
        self.menu.sudo().write({"pick_by_product": True})
        product_lot = (
            self.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product Lot",
                    "type": "product",
                    "tracking": "lot",
                    "barcode": "LOT",
                    "default_code": "LOT",
                }
            )
        )
        batch = self._create_picking_batch(
            [
                [self.BatchProduct(product=product_lot, quantity=10)],
                [self.BatchProduct(product=product_lot, quantity=20)],
            ]
        )
        self._simulate_batch_selected(batch, in_lot=True)

        # Confirm start should go to start_line, not start_product
        response = self.service.dispatch(
            "confirm_start",
            params={"picking_batch_id": batch.id},
        )
        self.assertEqual(response["next_state"], "start_line")

    def test_scan_line_still_works_for_non_aggregatable_lines(self):
        """scan_line endpoint works normally for lines not in product scan."""
        product_lot = (
            self.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product Lot",
                    "type": "product",
                    "tracking": "lot",
                    "barcode": "LOT",
                    "default_code": "LOT",
                }
            )
        )
        batch = self._create_picking_batch(
            [
                [self.BatchProduct(product=product_lot, quantity=10)],
            ]
        )
        self._simulate_batch_selected(batch, in_lot=True)
        self.menu.sudo().write({"pick_by_product": True})

        response = self.service.dispatch(
            "confirm_start",
            params={"picking_batch_id": batch.id},
        )
        self.assertEqual(response["next_state"], "start_line")

        line = batch.picking_ids.move_line_ids[0]
        response = self.service.dispatch(
            "scan_line",
            params={
                "picking_batch_id": batch.id,
                "move_line_id": line.id,
                "barcode": product_lot.barcode,
            },
        )
        self.assertEqual(response["next_state"], "scan_destination")

    def test_feature_off_behaves_normally(self):
        """With feature disabled, original flow is unchanged."""
        self.menu.sudo().write({"pick_by_product": False})
        batch = self._create_picking_batch(
            [
                [self.BatchProduct(product=self.product_a, quantity=10)],
                [self.BatchProduct(product=self.product_a, quantity=20)],
            ]
        )
        self._simulate_batch_selected(batch)

        response = self.service.dispatch(
            "confirm_start",
            params={"picking_batch_id": batch.id},
        )
        self.assertEqual(response["next_state"], "start_line")

    def test_start_product_shows_expected_data(self):
        """start_product shows product info, total qty, and lines."""
        response = self.service.dispatch(
            "confirm_start",
            params={"picking_batch_id": self.batch.id},
        )
        data = response["data"]["start_product"]
        self.assertEqual(data["product"]["id"], self.product_a.id)
        self.assertEqual(data["quantity"], 35.0)
        self.assertEqual(len(data["lines"]), 3)
        for line_data in data["lines"]:
            self.assertIn("id", line_data)
            self.assertIn("picking", line_data)
            self.assertIn("product_uom_qty", line_data)
            self.assertIn("qty_done", line_data)
        self.assertIn("batch", data)

    def test_next_product_shown_after_scan_complete(self):
        """After processing one product, the next aggregatable product is shown."""
        self.service.dispatch(
            "confirm_start",
            params={"picking_batch_id": self.batch.id},
        )
        self.service.dispatch(
            "scan_product",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.product_a.barcode,
            },
        )
        bin1 = self.env["stock.quant.package"].create({})
        response = self.service.dispatch(
            "scan_product_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "product_id": self.product_a.id,
                "location_id": self.stock_location.id,
                "barcode": bin1.name,
                "quantity": 35.0,
            },
        )

        self.assertEqual(response["next_state"], "start_product")
        self.assertEqual(
            response["data"]["start_product"]["product"]["id"], self.product_b.id
        )
