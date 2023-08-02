# Copyright 2022 Camptocamp SA
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields
from odoo.tests.common import TransactionCase


class CommonFlow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        ref = cls.env.ref
        cls.wh = ref("stock.warehouse0")
        cls.company = cls.wh.company_id
        cls.loc_stock = cls.wh.lot_stock_id
        cls.loc_customer = cls.env.ref("stock.stock_location_customers")
        cls.product = ref("product.product_product_9")
        cls._update_qty_in_location(cls.loc_stock, cls.product, 10)
        cls.env["stock.warehouse.flow"].search([]).action_generate_route()

    def _get_flow(self, delivery_steps):
        return self.env.ref(
            f"stock_warehouse_flow.stock_warehouse_flow_delivery_{delivery_steps}"
        )

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

    def _run_procurement(self, product, qty, carrier=None):
        proc_group = self.env["procurement.group"]
        uom = product.uom_id
        proc_qty, proc_uom = uom._adjust_uom_quantities(qty, uom)
        today = fields.Date.today()
        proc_group = self.env["procurement.group"].create(
            {"carrier_id": carrier.id if carrier else False}
        )
        values = {
            "group_id": proc_group,
            "date_planned": today,
            "date_deadline": today,
            "warehouse_id": self.wh or False,
            "company_id": self.company,
        }
        procurement = proc_group.Procurement(
            product,
            proc_qty,
            proc_uom,
            self.loc_customer,
            product.name,
            "PROC TEST",
            self.company,
            values,
        )
        proc_group.run([procurement])

    def _validate_picking(self, picking):
        for move_line in picking.move_line_ids:
            move_line.qty_done = move_line.reserved_uom_qty
        picking._action_done()

    def _prepare_split_test(self, qty=None):
        ship_flow = self._get_flow("ship_only")
        ship_flow.sequence = 100
        pick_flow = self._get_flow("pick_ship")
        pick_flow.write(
            {
                "sequence": 1,
                "split_method": "simple",
                "qty": qty or 2,
                "carrier_ids": [(6, 0, ship_flow.carrier_ids.ids)],
            }
        )
        return ship_flow, pick_flow

    def _run_split_flow(self, qty=None):
        pick_flow = self._get_flow("pick_ship")
        moves_before = self.env["stock.move"].search([])
        self._run_procurement(self.product, qty or 5, pick_flow.carrier_ids)
        moves_after = self.env["stock.move"].search([])
        return (moves_after - moves_before).sorted(lambda m: m.id)
