# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields
from odoo.tests import common


class PromiseReleaseCommonCase(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.wh = cls.env["stock.warehouse"].create(
            {
                "name": "Test Warehouse",
                "reception_steps": "one_step",
                "delivery_steps": "pick_ship",
                "code": "WHTEST",
            }
        )
        cls.loc_stock = cls.wh.lot_stock_id
        cls.loc_customer = cls.env.ref("stock.stock_location_customers")
        cls.product1 = cls.env["product.product"].create(
            {"name": "Product 1", "type": "product"}
        )
        cls.product2 = cls.env["product.product"].create(
            {"name": "Product 2", "type": "product"}
        )
        cls.product3 = cls.env["product.product"].create(
            {"name": "Product 3", "type": "product"}
        )
        cls.product4 = cls.env["product.product"].create(
            {"name": "Product 4", "type": "product"}
        )
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.partner_delta = cls.env.ref("base.res_partner_4")
        cls.loc_bin1 = cls.env["stock.location"].create(
            {"name": "Bin1", "location_id": cls.loc_stock.id}
        )

    @classmethod
    def _create_picking_chain(cls, wh, products=None, date=None, move_type="direct"):
        """Create picking chain

        It runs the procurement group to create the moves required for
        a product. According to the WH, it creates the pick+ship
        moves.

        Products must be a list of tuples (product, quantity) or
        (product, quantity, uom).
        One stock move will be created for each tuple.
        """

        if products is None:
            products = []

        group = cls.env["procurement.group"].create(
            {
                "name": "TEST",
                "move_type": move_type,
                "partner_id": cls.partner_delta.id,
            }
        )
        values = {
            "company_id": wh.company_id,
            "group_id": group,
            "date_planned": date or fields.Datetime.now(),
            "warehouse_id": wh,
        }

        for row in products:
            if len(row) == 2:
                product, qty = row
                uom = product.uom_id
            elif len(row) == 3:
                product, qty, uom = row
            else:
                raise ValueError(
                    "Expect (product, quantity, uom) or (product, quantity)"
                )

            cls.env["procurement.group"].run(
                [
                    cls.env["procurement.group"].Procurement(
                        product,
                        qty,
                        uom,
                        cls.loc_customer,
                        "TEST",
                        "TEST",
                        wh.company_id,
                        values,
                    )
                ]
            )
        pickings = cls._pickings_in_group(group)
        pickings.mapped("move_lines").write(
            {"date_priority": date or fields.Datetime.now()}
        )
        return pickings

    @classmethod
    def _pickings_in_group(cls, group):
        return cls.env["stock.picking"].search([("group_id", "=", group.id)])

    @classmethod
    def _update_qty_in_location(cls, location, product, quantity):
        quants = cls.env["stock.quant"]._gather(product, location, strict=True)
        # this method adds the quantity to the current quantity, so remove it
        quantity -= sum(quants.mapped("quantity"))
        cls.env["stock.quant"]._update_available_quantity(product, location, quantity)
        cls.env["product.product"].invalidate_cache(
            fnames=[
                "qty_available",
                "virtual_available",
                "incoming_qty",
                "outgoing_qty",
            ]
        )
