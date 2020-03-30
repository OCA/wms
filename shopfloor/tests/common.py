from collections import namedtuple
from contextlib import contextmanager
from pprint import pformat

from odoo import models
from odoo.tests.common import Form, SavepointCase

from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.component.core import WorkContext
from odoo.addons.component.tests.common import ComponentMixin


class AnyObject:
    def __repr__(self):
        return "ANY"

    def __deepcopy__(self, memodict=None):
        return self

    def __copy__(self):
        return self

    def __eq__(self, other):
        return True


class CommonCase(SavepointCase, ComponentMixin):

    # by default disable tracking suite-wise, it's a time saver :)
    tracking_disable = True

    ANY = AnyObject()

    @contextmanager
    def work_on_services(self, **params):
        params = params or {}
        collection = _PseudoCollection("shopfloor.service", self.env)
        yield WorkContext(
            model_name="rest.service.registration", collection=collection, **params
        )

    @contextmanager
    def work_on_actions(self, **params):
        params = params or {}
        collection = _PseudoCollection("shopfloor.action", self.env)
        yield WorkContext(
            model_name="rest.service.registration", collection=collection, **params
        )

    # pylint: disable=method-required-super
    # super is called "the old-style way" to call both super classes in the
    # order we want
    def setUp(self):
        # Have to initialize both odoo env and stuff +
        # the Component registry of the mixin
        SavepointCase.setUp(self)
        ComponentMixin.setUp(self)

    @classmethod
    def setUpClass(cls):
        super(CommonCase, cls).setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=cls.tracking_disable)
        )
        cls.setUpComponent()
        cls.setUpClassVars()
        cls.setUpClassBaseData()

    @classmethod
    def setUpClassVars(cls):
        stock_location = cls.env.ref("stock.stock_location_stock")
        cls.stock_location = stock_location
        cls.dispatch_location = cls.env.ref("stock.location_dispatch_zone")
        cls.dispatch_location.barcode = "DISPATCH"
        cls.packing_location = cls.env.ref("stock.location_pack_zone")
        cls.input_location = cls.env.ref("stock.stock_location_company")
        cls.shelf1 = cls.env.ref("stock.stock_location_components")
        cls.shelf2 = cls.env.ref("stock.stock_location_14")
        cls.customer = cls.env["res.partner"].create({"name": "Customer"})

    @classmethod
    def setUpClassBaseData(cls):
        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Product A",
                "type": "product",
                "default_code": "A",
                "barcode": "A",
                "weight": 2,
            }
        )
        cls.product_a_packaging = cls.env["product.packaging"].create(
            {"name": "Box", "product_id": cls.product_a.id, "barcode": "ProductABox"}
        )
        cls.product_b = cls.env["product.product"].create(
            {
                "name": "Product B",
                "type": "product",
                "default_code": "B",
                "barcode": "B",
                "weight": 3,
            }
        )
        cls.product_b_packaging = cls.env["product.packaging"].create(
            {"name": "Box", "product_id": cls.product_b.id, "barcode": "ProductBBox"}
        )
        cls.product_c = cls.env["product.product"].create(
            {
                "name": "Product C",
                "type": "product",
                "default_code": "C",
                "barcode": "C",
                "weight": 3,
            }
        )
        cls.product_c_packaging = cls.env["product.packaging"].create(
            {"name": "Box", "product_id": cls.product_b.id, "barcode": "ProductCBox"}
        )
        cls.product_d = cls.env["product.product"].create(
            {
                "name": "Product D",
                "type": "product",
                "default_code": "D",
                "barcode": "D",
                "weight": 3,
            }
        )
        cls.product_d_packaging = cls.env["product.packaging"].create(
            {"name": "Box", "product_id": cls.product_d.id, "barcode": "ProductDBox"}
        )

    def assert_response(self, response, next_state=None, message=None, data=None):
        """Assert a response from the webservice

        The data and message dictionaries can use ``self.ANY`` to accept any
        value.
        """
        expected = {}
        if message:
            expected["message"] = message
        if next_state:
            expected.update(
                {"next_state": next_state, "data": {next_state: data or {}}}
            )
        elif data:
            expected["data"] = data
        self.assertDictEqual(
            response,
            expected,
            "\n\nActual:\n%s"
            "\n\nExpected:\n%s" % (pformat(response), pformat(expected)),
        )

    @classmethod
    def _create_picking(cls, picking_type=None, lines=None, confirm=True):
        picking_form = Form(cls.env["stock.picking"])
        picking_form.picking_type_id = picking_type or cls.picking_type
        picking_form.partner_id = cls.customer
        if lines is None:
            lines = [(cls.product_a, 10), (cls.product_b, 10)]
        for product, qty in lines:
            with picking_form.move_ids_without_package.new() as move:
                move.product_id = product
                move.product_uom_qty = qty
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
    def _fill_stock_for_moves(cls, moves, in_package=False, in_lot=False):
        product_locations = {}
        package = None
        if in_package:
            package = cls.env["stock.quant.package"].create({})
        for move in moves:
            key = (move.product_id, move.location_id)
            product_locations.setdefault(key, 0)
            product_locations[key] += move.product_qty
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
        batch_form = Form(cls.env["stock.picking.batch"])
        for transfer in products:
            picking_form = Form(cls.env["stock.picking"])
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
