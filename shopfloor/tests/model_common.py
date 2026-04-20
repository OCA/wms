# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("-at_install", "post_install")
class ModelCommon(TransactionCase):
    """Common class to test model code"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.setUpClassData()

    @classmethod
    def setUpClassData(cls):
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.pack_location = cls.warehouse.wh_pack_stock_loc_id
        cls.ship_location = cls.warehouse.wh_output_stock_loc_id
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        # Create products
        cls.product_a = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product A",
                    "is_storable": True,
                    "default_code": "A",
                    "barcode": "A",
                    "weight": 2,
                }
            )
        )
        cls.product_a_packaging = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "Box",
                    "product_id": cls.product_a.id,
                    "barcode": "ProductABox",
                }
            )
        )
        cls.product_b = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product B",
                    "is_storable": True,
                    "default_code": "B",
                    "barcode": "B",
                    "weight": 2,
                }
            )
        )
        cls.product_b_packaging = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "Box",
                    "product_id": cls.product_b.id,
                    "barcode": "ProductBBox",
                }
            )
        )
        # Put product_a quantities in different packages to get several move lines
        cls.package_1 = cls.env["stock.quant.package"].create({"name": "PACKAGE_1"})
        cls.package_2 = cls.env["stock.quant.package"].create({"name": "PACKAGE_2"})
        cls.package_3 = cls.env["stock.quant.package"].create({"name": "PACKAGE_3"})
        cls.package_4 = cls.env["stock.quant.package"].create({"name": "PACKAGE_4"})

    @classmethod
    def _update_qty_in_location(
        cls, location, product, quantity, package=None, lot=None
    ):
        quants = cls.env["stock.quant"]._gather(
            product, location, lot_id=lot, package_id=package, strict=True
        )
        # this method adds the quantity to the current quantity, so remove it
        quantity -= sum(quants.mapped("quantity"))
        if not quantity:
            return
        cls.env["stock.quant"]._update_available_quantity(
            product, location, quantity=quantity, package_id=package, lot_id=lot
        )

    @classmethod
    def _create_picking(cls, picking_type=None, lines=None, confirm=True, **kw):
        picking_form = Form(cls.env["stock.picking"])
        picking_form.picking_type_id = picking_type or cls.picking_type
        picking_form.partner_id = cls.customer
        if lines is None:
            lines = [(cls.product_a, 10), (cls.product_b, 10)]
        for product, qty in lines:
            with picking_form.move_ids_without_package.new() as move:
                move.product_id = product
                move.product_uom_qty = qty
        for k, v in kw.items():
            setattr(picking_form, k, v)
        picking = picking_form.save()
        if confirm:
            picking.action_confirm()
        return picking
