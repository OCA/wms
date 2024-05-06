# Copyright 2023 Camptocamp SA
# Copyright 2024 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests import Form

from .common import CommonCase


class CommonCaseReturn(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # In order to have the `picking_type_reception_demo` picking_type
        # on returned pickings and moves
        cls.reception_type = cls.env.ref(
            "shopfloor_reception.picking_type_reception_demo"
        )
        ship_type = cls.env.ref("stock.picking_type_out")
        ship_type.sudo().return_picking_type_id = cls.reception_type
        cls.location_src = cls.env.ref("stock.stock_location_stock")
        cls.location_dest = cls.env.ref("stock.stock_location_company")
        cls.location = cls.location_src
        cls.product = cls.product_a
        cls.order = cls.create_sale_order()
        cls._add_stock_to_product(cls.product, cls.location, 20.0)
        packaging_ids = [
            cls.product_a_packaging.id,
            cls.product_c_packaging.id,
            cls.product_b_packaging.id,
            cls.product_d_packaging.id,
        ]
        packagings = cls.env["product.packaging"].browse(packaging_ids)
        packagings.write({"qty": 10.0})

    @classmethod
    def _shopfloor_user_values(cls):
        vals = super()._shopfloor_user_values()
        group_ids = vals.get("groups_id")
        if group_ids:
            ids = group_ids[0][2]
        else:
            ids = []
        ids.append(cls.env.ref("sales_team.group_sale_salesman").id)
        vals["groups_id"] = [(6, 0, ids)]
        return vals

    @classmethod
    def create_sale_order(cls):
        form = Form(cls.env["sale.order"])
        form.partner_id = cls.customer
        lines = [(cls.product, 20)]
        for product, qty in lines:
            with form.order_line.new() as line:
                line.product_id = product
                line.product_uom_qty = qty
        return form.save()

    @classmethod
    def create_delivery(cls):
        cls.order.action_confirm()
        cls.cache_existing_record_ids()
        return cls.order.picking_ids

    @classmethod
    def _add_package_to_order(cls, order):
        packaging_ids = [
            cls.product_a_packaging.id,
            cls.product_c_packaging.id,
            cls.product_b_packaging.id,
            cls.product_d_packaging.id,
        ]
        packagings = cls.env["product.packaging"].browse(packaging_ids)
        for line in order.order_line:
            product = line.product_id
            packaging = packagings.filtered(lambda p: p.product_id == product)
            line.product_packaging = packaging

    @classmethod
    def deliver(cls, pickings):
        while "there's a ready picking":
            ready_picking = pickings.filtered(
                lambda p: p.state in ("ready", "confirmed", "assigned")
            )
            if not ready_picking:
                break
            for line in ready_picking.move_line_ids:
                line.qty_done = line.product_qty
            ready_picking._action_done()

    @classmethod
    def partial_deliver(cls, picking, qty_done):
        picking.move_line_ids.write({"qty_done": qty_done})
        action_data = picking.button_validate()
        if not action_data or action_data is True:
            return picking.browse()
        backorder_wizard = Form(
            cls.env["stock.backorder.confirmation"].with_context(action_data["context"])
        ).save()
        backorder_wizard.process()
        return cls.env["stock.picking"].search([("backorder_id", "=", picking.id)])

    def assert_return_of(self, picking_in, origin):
        self.assertEqual(origin, picking_in.origin)
        self.assertEqual(
            picking_in.location_dest_id, self.reception_type.default_location_dest_id
        )
        self.assertEqual(
            picking_in.location_id, self.reception_type.default_location_src_id
        )

    @classmethod
    def cache_existing_record_ids(cls):
        # store ids of pickings, moves and move lines already created before
        # tests are run.
        cls.existing_picking_ids = cls.env["stock.picking"].search([]).ids
        cls.existing_move_ids = cls.env["stock.move"].search([]).ids
        cls.existing_move_line_ids = cls.env["stock.move.line"].search([]).ids

    @classmethod
    def get_new_pickings(cls):
        res = cls.env["stock.picking"].search(
            [("id", "not in", cls.existing_picking_ids)]
        )
        cls.cache_existing_record_ids()
        return res

    @classmethod
    def get_new_move_lines(cls):
        res = cls.env["stock.move.line"].search(
            [("id", "not in", cls.existing_move_line_ids)]
        )
        cls.cache_existing_record_ids()
        return res

    @classmethod
    def _add_stock_to_product(cls, product, location, qty):
        """Set the stock quantity of the product."""
        values = {
            "product_id": product.id,
            "location_id": location.id,
            "inventory_quantity": qty,
        }
        cls.env["stock.quant"].sudo().with_context(inventory_mode=True).create(values)
        cls.cache_existing_record_ids()

    @classmethod
    def _enable_allow_return(cls):
        cls.menu.sudo().allow_return = True
