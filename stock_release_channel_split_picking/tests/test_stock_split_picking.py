# Copyright 2017 Tecnativa - Vicent Cubells <vicent.cubells@tecnativa.com>
# Copyright 2018 Camptocamp SA - Julien Coux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import RecordCapturer, TransactionCase

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestStockSplitPicking(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestStockSplitPicking, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))

        cls.src_location = cls.env.ref("stock.stock_location_stock")
        cls.dest_location = cls.env.ref("stock.stock_location_customers")
        cls.product = cls.env["product.product"].create({"name": "Test product"})
        cls.product_2 = cls.env["product.product"].create({"name": "Test product 2"})
        cls.partner = cls.env["res.partner"].create({"name": "Test partner"})

        cls.default_channel = cls.env.ref(
            "stock_release_channel.stock_release_channel_default"
        )

        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.partner.id,
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "location_id": cls.src_location.id,
                "location_dest_id": cls.dest_location.id,
                "release_channel_id": cls.default_channel.id,
            }
        )

        def _create_stock_move(product):
            return cls.env["stock.move"].create(
                {
                    "name": "/",
                    "picking_id": cls.picking.id,
                    "product_id": product.id,
                    "product_uom_qty": 10,
                    "product_uom": product.uom_id.id,
                    "location_id": cls.src_location.id,
                    "location_dest_id": cls.dest_location.id,
                }
            )

        cls.move = _create_stock_move(cls.product)
        cls.move_2 = _create_stock_move(cls.product_2)

    def test_stock_split_picking_with_release_channel(self):
        with RecordCapturer(self.env["stock.picking"], []) as captured:
            wizard = (
                self.env["stock.split.picking"]
                .with_context(active_ids=self.picking.ids)
                .create({"mode": "move"})
            )
            wizard.action_apply()

        new_picking = captured.records
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking[0].release_channel_id, self.default_channel)
        move_pickings = self.move.mapped("picking_id") | self.move_2.mapped(
            "picking_id"
        )
        self.assertEqual(move_pickings, self.picking | new_picking)
