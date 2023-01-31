# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from collections import namedtuple

from odoo import models
from odoo.tests.common import Form

from odoo.addons.shopfloor_base.tests.common import CommonCase as BaseCommonCase


class CommonCase(BaseCommonCase):
    @classmethod
    def setUpShopfloorApp(cls):
        cls.shopfloor_app = cls.env.ref("shopfloor.app_demo").with_user(
            cls.shopfloor_user
        )

    @classmethod
    def setUpClassVars(cls):
        super().setUpClassVars()
        stock_location = cls.env.ref("stock.stock_location_stock")
        cls.stock_location = stock_location
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.dispatch_location = cls.env.ref("stock.location_dispatch_zone")
        cls.packing_location = cls.env.ref("stock.location_pack_zone")
        cls.input_location = cls.env.ref("stock.stock_location_company")
        cls.shelf1 = cls.env.ref("stock.stock_location_components")
        cls.shelf2 = cls.env.ref("stock.stock_location_14")

    @classmethod
    def _shopfloor_user_values(cls):
        vals = super()._shopfloor_user_values()
        vals["groups_id"] = [(6, 0, [cls.env.ref("stock.group_stock_user").id])]
        return vals

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.customer = cls.env["res.partner"].sudo().create({"name": "Customer"})

        cls.customer_location.sudo().barcode = "CUSTOMERS"
        cls.dispatch_location.sudo().barcode = "DISPATCH"
        cls.packing_location.sudo().barcode = "PACKING"
        cls.input_location.sudo().barcode = "INPUT"
        cls.shelf1.sudo().barcode = "SHELF1"
        cls.shelf2.sudo().barcode = "SHELF2"

        cls.product_a = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product A",
                    "type": "product",
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
                    "qty": 3.0,
                }
            )
        )
        cls.product_b = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product B",
                    "type": "product",
                    "default_code": "B",
                    "barcode": "B",
                    "weight": 3,
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
        cls.product_c = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product C",
                    "type": "product",
                    "default_code": "C",
                    "barcode": "C",
                    "weight": 3,
                }
            )
        )
        cls.product_c_packaging = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "Box",
                    "product_id": cls.product_c.id,
                    "barcode": "ProductCBox",
                    "qty": 3,
                }
            )
        )
        cls.product_d = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product D",
                    "type": "product",
                    "default_code": "D",
                    "barcode": "D",
                    "weight": 3,
                }
            )
        )
        cls.product_d_packaging = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "Box",
                    "product_id": cls.product_d.id,
                    "barcode": "ProductDBox",
                }
            )
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

    @classmethod
    def _update_qty_in_location(
        cls, location, product, quantity, package=None, lot=None
    ):
        quants = cls.env["stock.quant"]._gather(
            product, location, lot_id=lot, package_id=package, strict=True
        )
        # this method adds the quantity to the current quantity, so remove it
        quantity -= sum(quants.mapped("quantity"))
        cls.env["stock.quant"]._update_available_quantity(
            product, location, quantity, package_id=package, lot_id=lot
        )

    @classmethod
    def _fill_stock_for_moves(
        cls, moves, in_package=False, same_package=True, in_lot=False, location=False
    ):
        """Satisfy stock for given moves.

        :param moves: stock.move recordset
        :param in_package: stock.quant.package record or simple boolean
            If a package record is given, it will be used as package.
            If a boolean true is given, a new package will be created for each move.
        :param same_package:
            modify the behavior of `in_package` to use the same package for all moves.
        :param in_lot: stock.production.lot record or simple boolean
            If a lot record is given, it will be used as lot.
            If a boolean true is given, a new lot will be created.
        """
        product_packages = {}
        product_locations = {}
        package = None
        if in_package:
            if isinstance(in_package, models.BaseModel):
                package = in_package
            else:
                package = cls.env["stock.quant.package"].create({})
        for move in moves:
            key = (move.product_id, location or move.location_id)
            product_locations.setdefault(key, 0)
            product_locations[key] += move.product_qty
            if in_package:
                if isinstance(in_package, models.BaseModel):
                    package = in_package
                if not package or package and not same_package:
                    package = cls.env["stock.quant.package"].create({})
                product_packages[key] = package
        for (product, location), qty in product_locations.items():
            lot = None
            if in_lot:
                if isinstance(in_lot, models.BaseModel):
                    lot = in_lot
                else:
                    lot = cls.env["stock.production.lot"].create(
                        {"product_id": product.id, "company_id": cls.env.company.id}
                    )
            if not (in_lot or in_package):
                # always add more quantity in stock to avoid to trigger the
                # "zero checks" in tests, not for lots which must have a qty
                # of 1 and not for packages because we need the strict number
                # of units to pick a package
                qty *= 2
            cls._update_qty_in_location(
                location, product, qty, package=package, lot=lot
            )

    # used by _create_package_in_location
    PackageContent = namedtuple(
        "PackageContent",
        # recordset of the product,
        # quantity in float
        # recordset of the lot (optional)
        "product quantity lot",
    )

    def _create_package_in_location(self, location, content):
        """Create a package and quants in a location

        content is a list of PackageContent
        """
        package = self.env["stock.quant.package"].create({})
        for product, quantity, lot in content:
            self._update_qty_in_location(
                location, product, quantity, package=package, lot=lot
            )
        return package

    def _create_lot(self, product):
        return self.env["stock.production.lot"].create(
            {"product_id": product.id, "company_id": self.env.company.id}
        )


class PickingBatchMixin:

    BatchProduct = namedtuple(
        "BatchProduct",
        # browse record of the product,
        # quantity in float
        "product quantity",
    )

    @classmethod
    def _create_picking_batch(cls, products):
        """Create a picking batch

        :param products: list of list of BatchProduct. The outer list creates
        pickings and the innerr list creates moves in these pickings
        """
        batch_form = Form(cls.env["stock.picking.batch"].sudo())
        for transfer in products:
            picking_form = Form(cls.env["stock.picking"].sudo())
            picking_form.picking_type_id = cls.picking_type
            picking_form.location_id = cls.stock_location
            picking_form.location_dest_id = cls.packing_location
            picking_form.origin = "test"
            picking_form.partner_id = cls.customer
            for batch_product in transfer:
                product = batch_product.product
                quantity = batch_product.quantity
                with picking_form.move_ids_without_package.new() as move:
                    move.product_id = product
                    move.product_uom_qty = quantity
            picking = picking_form.save()
            batch_form.picking_ids.add(picking)

        batch = batch_form.save()
        batch.picking_ids.action_confirm()
        batch.picking_ids.action_assign()
        return batch

    @classmethod
    def _simulate_batch_selected(
        cls, batches, in_package=False, in_lot=False, fill_stock=True
    ):
        """Create a state as if a batch was selected by the user

        * The picking batch is in progress
        * It is assigned to the current user
        * All the move lines are available

        Note: currently, this method create a source package that contains
        all the products of the batch. It is enough for the current tests.
        """
        pickings = batches.mapped("picking_ids")
        if fill_stock:
            cls._fill_stock_for_moves(
                pickings.mapped("move_lines"), in_package=in_package, in_lot=in_lot
            )
        pickings.action_assign()
        batches.write({"state": "in_progress", "user_id": cls.env.uid})
