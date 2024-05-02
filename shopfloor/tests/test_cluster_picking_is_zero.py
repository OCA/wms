# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_cluster_picking_base import ClusterPickingCommonCase

# pylint: disable=missing-return


class ClusterPickingIsZeroCase(ClusterPickingCommonCase):
    """Tests covering the /is_zero endpoint

    After a line has been scanned, if the location is empty, the
    client application is redirected to the "zero_check" state,
    where the user has to confirm or not that the location is empty.
    When the location is empty, there is nothing to do, but when it
    in fact not empty, a draft inventory must be created for the
    product so someone can verify.
    """

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.batch = cls._create_picking_batch(
            [
                [
                    cls.BatchProduct(product=cls.product_a, quantity=10),
                    cls.BatchProduct(product=cls.product_b, quantity=10),
                ]
            ]
        )
        cls.picking = cls.batch.picking_ids
        cls._simulate_batch_selected(cls.batch)

        cls.line = cls.picking.move_line_ids[0]
        cls.next_line = cls.picking.move_line_ids[1]
        cls.bin1 = cls.env["stock.quant.package"].create({})
        cls._update_qty_in_location(
            cls.line.location_id, cls.line.product_id, cls.line.reserved_uom_qty
        )
        # we already scan and put the first line in bin1, at this point the
        # system see the location is empty and reach "zero_check"
        cls._set_dest_package_and_done(cls.line, cls.bin1)

    def test_is_zero_is_empty(self):
        """call /is_zero confirming it's empty"""
        response = self.service.dispatch(
            "is_zero",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": self.line.id,
                "zero": True,
            },
        )
        self.assert_response(
            response,
            next_state="start_line",
            data=self._line_data(self.next_line),
            message={
                "message_type": "success",
                "body": "{} {} put in {}".format(
                    self.line.qty_done,
                    self.line.product_id.display_name,
                    self.bin1.name,
                ),
            },
        )

    def test_is_zero_is_not_empty(self):
        """call /is_zero not confirming it's empty"""
        response = self.service.dispatch(
            "is_zero",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": self.line.id,
                "zero": False,
            },
        )
        quant = self.env["stock.quant"].search(
            [
                ("location_id", "=", self.line.location_id.id),
                ("product_id", "=", self.line.product_id.id),
                ("inventory_quantity_set", "=", True),
            ]
        )
        self.assertTrue(quant)
        self.assert_response(
            response,
            next_state="start_line",
            data=self._line_data(self.next_line),
            message={
                "message_type": "success",
                "body": "{} {} put in {}".format(
                    self.line.qty_done,
                    self.line.product_id.display_name,
                    self.bin1.name,
                ),
            },
        )
