# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class CommonReleaseChannelBlock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.product = cls.env["product.product"].create(
            {"name": "product", "type": "product"}
        )
        cls.wh = cls.env.ref("stock.warehouse0")
        cls.loc_stock = cls.wh.lot_stock_id
        cls.loc_customer = cls.env.ref("stock.stock_location_customers")
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.loc_stock, 100.0
        )
        cls.partner = cls.env["res.partner"].create({"name": "Unittest partner"})

    @classmethod
    def _create_picking_out(cls, product_qty=100):
        # NOTE: Create delivery the same way a SO would do through a procurement.
        # This ensure moves will get a warehouse set, making the computation
        # of 'ordered_available_to_promise_qty' of 'stock_available_to_promise_release'
        # working as expected.
        proc_group = cls.env["procurement.group"].create(
            {
                "name": "TEST",
                "move_type": "direct",
                "partner_id": cls.partner.id,
            }
        )
        proc_values = {
            "group_id": proc_group,
            "date_planned": "2024-02-26",
            "date_deadline": "2024-02-26",
            "warehouse_id": cls.wh,
            "partner_id": cls.partner.id,
            "company_id": cls.wh.company_id,
        }
        proc = cls.env["procurement.group"].Procurement(
            cls.product,
            product_qty,
            cls.product.uom_id,
            cls.loc_customer,
            cls.product.display_name,
            "TEST",
            cls.wh.company_id,
            proc_values,
        )
        # Run the procurement and return the created delivery
        existing_moves = cls.env["stock.move"].search([])
        proc_group.run([proc])
        new_moves = cls.env["stock.move"].search([])
        return (new_moves - existing_moves).picking_id

    @classmethod
    def _do_picking(cls, picking, done_qty):
        picking.move_ids.quantity_done = done_qty
        picking._action_done()
