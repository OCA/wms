# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_cluster_picking_base import ClusterPickingCommonCase


class ClusterPickingScanDestinationPackPrefillQtyCase(ClusterPickingCommonCase):
    """Tests covering the /scan_destination_pack endpoint

    With the no prefill quantity option set

    """

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.menu.sudo().no_prefill_qty = True
        cls.batch = cls._create_picking_batch(
            [
                [
                    cls.BatchProduct(product=cls.product_a, quantity=10),
                    cls.BatchProduct(product=cls.product_b, quantity=10),
                ],
                [cls.BatchProduct(product=cls.product_a, quantity=10)],
            ]
        )
        cls.one_line_picking = cls.batch.picking_ids.filtered(
            lambda picking: len(picking.move_lines) == 1
        )
        cls.two_lines_picking = cls.batch.picking_ids.filtered(
            lambda picking: len(picking.move_lines) == 2
        )

        cls.bin1 = cls.env["stock.quant.package"].create({})
        cls.bin2 = cls.env["stock.quant.package"].create({})

        cls._simulate_batch_selected(cls.batch)

    def test_scan_destination_pack_increment_with_product(self):
        """Check quantity increment by scanning the product."""
        line = self.batch.picking_ids.move_line_ids[0]
        previous_qty_done = line.qty_done
        for qty_done in range(1, 2):
            response = self.service.dispatch(
                "scan_destination_pack",
                params={
                    "picking_batch_id": self.batch.id,
                    "move_line_id": line.id,
                    "barcode": line.product_id.barcode,
                    "quantity": qty_done,
                },
            )
            # Ensure the qty has not changed.
            self.assertEqual(line.qty_done, previous_qty_done)

            expected_qty_done = qty_done + 1
            self.assert_response(
                response,
                next_state="scan_destination",
                data=self._line_data(line, qty_done=expected_qty_done),
            )

    def test_scan_destination_pack_increment_with_wrong_product(self):
        """Check quantity is not incremented by scanning the wrong product."""
        line = self.batch.picking_ids.move_line_ids[0]
        previous_qty_done = line.qty_done
        qty_done = 2
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                "barcode": self.product_b.barcode,
                "quantity": qty_done,
            },
        )
        # Ensure the qty has not changed.
        self.assertEqual(line.qty_done, previous_qty_done)

        expected_qty_done = qty_done
        self.assert_response(
            response,
            next_state="scan_destination",
            data=self._line_data(line, qty_done=expected_qty_done),
            message=self.service.msg_store.bin_not_found_for_barcode(
                self.product_b.barcode
            ),
        )

    def test_scan_destination_pack_increment_with_packaging(self):
        """Check quantity incremented by scanning the packaging."""
        line = self.batch.picking_ids.move_line_ids[0]
        previous_qty_done = line.qty_done
        packaging = self.product_a_packaging
        qty_done = 2
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                "barcode": packaging.barcode,
                "quantity": qty_done,
            },
        )
        # Ensure the qty has not changed in the record.
        self.assertEqual(line.qty_done, previous_qty_done)

        expected_qty_done = qty_done + packaging.qty
        self.assert_response(
            response,
            next_state="scan_destination",
            data=self._line_data(line, qty_done=expected_qty_done),
        )
