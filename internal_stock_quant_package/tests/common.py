# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.tests.common import TransactionCase


class TestStockPickingInternal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context, tracking_disable=True, test_queue_job_no_delay=True
            )
        )

        cls.picking_type_out = cls.env.ref("stock.picking_type_out")
        cls.picking_type_out.empty_internal_package_on_transfer = True
        cls.internal_package = cls.env["stock.quant.package"].create(
            {"is_internal": True}
        )
        cls.external_package = cls.env["stock.quant.package"].create({})
        cls.product_a = cls.env["product.product"].create(
            {"name": "Product A", "type": "product"}
        )
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.picking_type_out.id,
                "location_dest_id": cls.customer_location.id,
                "location_id": cls.stock_location.id,
            }
        )
        cls.env["stock.move"].create(
            {
                "name": cls.product_a.name,
                "product_id": cls.product_a.id,
                "product_uom_qty": 1,
                "product_uom": cls.product_a.uom_id.id,
                "picking_id": cls.picking.id,
                "location_dest_id": cls.customer_location.id,
                "location_id": cls.stock_location.id,
            }
        )
        wiz = cls.env["stock.change.product.qty"].create(
            {
                "product_id": cls.product_a.id,
                "product_tmpl_id": cls.product_a.product_tmpl_id.id,
                "new_quantity": 1,
            }
        )
        wiz.change_product_qty()

        cls.picking.action_assign()
