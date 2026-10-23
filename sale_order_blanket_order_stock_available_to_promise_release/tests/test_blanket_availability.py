# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import Form, new_test_user, tagged

from odoo.addons.sale_order_blanket_order_stock_prebook_release.tests.common import (
    SaleOrderBlanketOrderStockPrebookReleaseCase,
)


@tagged("post_install", "-at_install")
class TestBlanketAvailability(SaleOrderBlanketOrderStockPrebookReleaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._update_qty_in_location(cls.loc_bin1, cls.product1, 7.0)
        cls.blanket_so.write(
            {
                "warehouse_id": cls.wh.id,
                "blanket_validity_start_date": fields.Date.today(),
                "blanket_validity_end_date": fields.Date.add(
                    fields.Date.today(), years=1
                ),
            }
        )
        cls.blanket_so.action_confirm()

    def _create_blanket_order(self, product, qty, strategy, **values):
        blanket_so = self.env["sale.order"].create(
            {
                "order_type": "blanket",
                "partner_id": self.partner_delta.id,
                "warehouse_id": self.wh.id,
                "blanket_validity_start_date": fields.Date.today(),
                "blanket_validity_end_date": fields.Date.add(
                    fields.Date.today(), years=1
                ),
                "blanket_reservation_strategy": strategy,
                "order_line": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_uom_qty": qty,
                            "price_unit": 100.0,
                        }
                    ),
                ],
                **values,
            }
        )
        blanket_so.action_confirm()
        return blanket_so

    def _create_call_off_order(self, blanket_so, product, qty):
        call_off_so = self.env["sale.order"].create(
            {
                "order_type": "call_off",
                "partner_id": self.partner_delta.id,
                "blanket_order_id": blanket_so.id,
                "warehouse_id": blanket_so.warehouse_id.id,
                "company_id": blanket_so.company_id.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_uom_qty": qty,
                            "price_unit": 0.0,
                        }
                    ),
                ],
            }
        )
        call_off_so.action_confirm()
        return call_off_so

    def _create_stock_move(
        self,
        product,
        qty,
        sale_line=False,
        last_release_date=False,
        picking_type=None,
    ):
        picking_type = picking_type or self.wh.out_type_id
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": self.loc_stock.id,
                "location_dest_id": self.loc_customer.id,
                "partner_id": self.partner_delta.id,
                "last_release_date": last_release_date,
            }
        )
        move_values = {
            "name": product.display_name,
            "product_id": product.id,
            "product_uom_qty": qty,
            "product_uom": product.uom_id.id,
            "picking_id": picking.id,
            "picking_type_id": picking_type.id,
            "location_id": self.loc_stock.id,
            "location_dest_id": self.loc_customer.id,
            "company_id": self.wh.company_id.id,
        }
        if sale_line:
            move_values["sale_line_id"] = sale_line.id
        move = self.env["stock.move"].create(move_values)
        move._action_confirm()
        return move

    def test_blanket_availability_uses_call_off_remaining_qty(self):
        line = self.blanket_so.order_line
        self.assertEqual(line.availability_status, "partial")
        self._create_call_off_order(self.blanket_so, self.product1, 6.0)

        line.invalidate_recordset(
            ["availability_status", "available_qty", "delayed_qty"]
        )
        self.assertEqual(line.call_off_remaining_qty, 4.0)
        self.assertEqual(line.availability_status, "full")
        self.assertEqual(line.available_qty, 4.0)
        self.assertEqual(line.delayed_qty, 0.0)

    def test_at_confirm_uses_only_prebook_reservation_moves(self):
        line = self.blanket_so.order_line
        move = self._create_stock_move(
            self.product1,
            10.0,
            sale_line=line,
            last_release_date=fields.Datetime.now(),
            picking_type=self.wh.int_type_id,
        )

        line.invalidate_recordset(["move_ids", "availability_status", "available_qty"])
        self.assertIn(move, line.move_ids)
        self.assertFalse(move.used_for_sale_reservation)
        self.assertEqual(line.availability_status, "partial")
        self.assertEqual(line.available_qty, 7.0)

    def test_prebook_availability_without_release_or_physical_reservation(self):
        line = self.blanket_so.order_line
        moves = line._get_availability_moves()
        self.assertTrue(moves)
        moves.write({"need_release": False})
        self.assertFalse(any(moves.mapped("reserved_availability")))
        self.assertEqual(line.availability_status, "partial")
        self.assertEqual(line.available_qty, 7.0)

    def test_blanket_availability_without_remaining_qty(self):
        line = self.blanket_so.order_line
        self._create_call_off_order(self.blanket_so, self.product1, 10.0)

        line.invalidate_recordset(
            ["availability_status", "available_qty", "delayed_qty"]
        )
        self.assertEqual(line.call_off_remaining_qty, 0.0)
        self.assertEqual(line.availability_status, "full")
        self.assertEqual(line.available_qty, 0.0)
        self.assertEqual(line.delayed_qty, 0.0)

    def test_call_off_wizard_displays_blanket_availability(self):
        wizard_action = self.blanket_so.action_deliver_remaining()
        wizard = self.env["sale.order.deliver.remaining.wizard"].browse(
            wizard_action["res_id"]
        )
        wizard_line = wizard.wizard_line_ids.filtered(
            lambda item: item.sale_order_line_id == self.blanket_so.order_line
        )
        self.assertEqual(wizard_line.availability_status, "partial")
        self.assertEqual(
            wizard_line.available_qty,
            self.blanket_so.order_line.available_qty,
        )
        self.assertEqual(
            wizard_line.delayed_qty,
            self.blanket_so.order_line.delayed_qty,
        )
        self.assertEqual(
            wizard_line.expected_availability_date,
            self.blanket_so.order_line.expected_availability_date,
        )

    def test_at_call_off_without_reservation_moves_has_no_available_quantity(self):
        """warehouse stock alone does not supply move-based blanket availability"""
        self._update_qty_in_location(self.loc_bin1, self.product2, 7.0)
        blanket = self._create_blanket_order(self.product2, 10.0, "at_call_off")
        line = blanket.order_line
        self.assertFalse(line.move_ids)
        self.assertEqual(line.availability_status, "no")
        self.assertEqual(line.available_qty, 0.0)
        self.assertEqual(line.delayed_qty, 10.0)

    def test_at_call_off_no_stock(self):
        blanket_so = self._create_blanket_order(self.product4, 10.0, "at_call_off")

        line = blanket_so.order_line
        self.assertEqual(line.availability_status, "no")
        self.assertEqual(line.available_qty, 0.0)
        self.assertEqual(line.delayed_qty, 10.0)

    def test_prebook_availability_uses_blanket_line_uom(self):
        """reservation availability and the remaining quantity share the line uom"""
        self._update_qty_in_location(self.loc_bin1, self.product2, 18.0)
        dozen = self.env.ref("uom.product_uom_dozen")
        blanket = self._create_blanket_order(
            self.product2,
            3.0,
            "at_confirm",
            order_line=[
                Command.create(
                    {
                        "product_id": self.product2.id,
                        "product_uom": dozen.id,
                        "product_uom_qty": 3.0,
                    }
                )
            ],
        )
        line = blanket.order_line
        self.assertEqual(
            sum(line._get_availability_moves().mapped("product_qty")), 36.0
        )
        self.assertEqual(line.availability_status, "partial")
        self.assertEqual(line.available_qty, 1.5)
        self.assertEqual(line.delayed_qty, 1.5)

    def test_products_without_stock_reservation_are_fully_available(self):
        for product_type in ("service", "consu"):
            with self.subTest(product_type=product_type):
                product = self.env["product.product"].create(
                    {"name": "Blanket Non-storable", "type": product_type}
                )
                blanket_so = self._create_blanket_order(product, 10.0, "at_call_off")
                line = blanket_so.order_line
                self.assertEqual(line.availability_status, "full")
                self.assertEqual(line.available_qty, 10.0)
                self.assertEqual(line.delayed_qty, 0.0)

    def test_at_confirm_excludes_inactive_reservations(self):
        """inactive reservations must not contribute released quantities"""
        line = self.blanket_so.order_line
        move = self._create_stock_move(
            self.product1,
            10.0,
            sale_line=line,
            last_release_date=fields.Datetime.now(),
        )
        move.used_for_sale_reservation = True
        for state in ("draft", "done", "cancel"):
            with self.subTest(state=state):
                move.state = state
                self.assertNotIn(move, line._get_availability_moves())

    def test_call_off_wizard_filter_and_creation(self):
        """filter by availability status and keep standard call-off quantities"""
        self._update_qty_in_location(self.loc_bin1, self.product2, 12.0)
        self._update_qty_in_location(self.loc_bin1, self.product3, 4.0)
        blanket = self._create_blanket_order(
            self.product2,
            10.0,
            "at_confirm",
            order_line=[
                Command.create({"product_id": product.id, "product_uom_qty": 10.0})
                for product in (self.product2, self.product3, self.product4)
            ],
        )
        action = blanket.action_deliver_remaining()
        wizard = self.env[action["res_model"]].browse(action["res_id"])
        self.assertEqual(len(wizard.wizard_line_ids), 3)
        for status, product in (
            ("full", self.product2),
            ("partial", self.product3),
            ("no", self.product4),
        ):
            with self.subTest(status=status):
                with Form(wizard) as wizard_form:
                    wizard_form.availability_filter = status
                self.assertEqual(wizard.wizard_line_ids.product_id, product)
                self.assertEqual(wizard.wizard_line_ids.qty_to_deliver, 10.0)
        with Form(wizard) as wizard_form:
            wizard_form.availability_filter = "all"
        self.assertEqual(len(wizard.wizard_line_ids), 3)
        with Form(wizard) as wizard_form:
            wizard_form.availability_filter = "partial"
        action = wizard.action_create_call_off()
        call_off = self.env["sale.order"].browse(action["res_id"])
        self.assertEqual(call_off.order_line.product_id, self.product3)
        self.assertEqual(call_off.order_line.product_uom_qty, 10.0)

    def test_call_off_wizard_all_lines_and_empty_filter(self):
        """all lines allows unavailable quantities, an empty filter creates no order"""
        blanket = self._create_blanket_order(self.product4, 10.0, "at_call_off")
        action = blanket.action_deliver_remaining()
        wizard = self.env[action["res_model"]].browse(action["res_id"])
        with Form(wizard) as wizard_form:
            wizard_form.availability_filter = "full"
        self.assertFalse(wizard.wizard_line_ids)
        with self.assertRaises(UserError):
            wizard.action_create_call_off()
        with Form(wizard) as wizard_form:
            wizard_form.availability_filter = "all"
        self.assertEqual(wizard.wizard_line_ids.qty_to_deliver, 10.0)
        action = wizard.action_create_call_off()
        call_off = self.env["sale.order"].browse(action["res_id"])
        self.assertEqual(call_off.order_line.product_uom_qty, 10.0)

    def test_prebook_availability_is_warehouse_scoped_for_sales_user(self):
        """stock and promises in another warehouse do not affect the sales preview"""
        other_wh = self.env["stock.warehouse"].create(
            {"name": "Other ATP Warehouse", "code": "ATPOTH"}
        )
        self._update_qty_in_location(self.loc_bin1, self.product2, 7.0)
        self._update_qty_in_location(other_wh.lot_stock_id, self.product2, 100.0)
        move = self._create_stock_move(self.product2, 50.0)
        move.location_id = other_wh.lot_stock_id
        blanket = self._create_blanket_order(self.product2, 10.0, "at_confirm")
        salesman = new_test_user(
            self.env,
            login="blanket_atp_salesman",
            groups="sales_team.group_sale_salesman",
        )
        blanket.user_id = salesman
        blanket = blanket.with_user(salesman)
        action = blanket.action_deliver_remaining()
        wizard = (
            self.env[action["res_model"]].with_user(salesman).browse(action["res_id"])
        )
        self.assertEqual(wizard.wizard_line_ids.available_qty, 7.0)
        self.assertEqual(wizard.wizard_line_ids.delayed_qty, 3.0)

    def test_prebook_availability_uses_order_company(self):
        """availability comes from reservation moves in the blanket company"""
        company = self.env["res.company"].create({"name": "Blanket ATP Company"})
        company_env = self.env(
            context=dict(self.env.context, allowed_company_ids=[company.id])
        )
        warehouse = company_env["stock.warehouse"].search(
            [("company_id", "=", company.id)], limit=1
        )
        self.assertTrue(warehouse)
        company_env["stock.quant"]._update_available_quantity(
            self.product2.with_env(company_env), warehouse.lot_stock_id, 4.0
        )
        self._update_qty_in_location(self.loc_bin1, self.product2, 100.0)
        blanket = self._create_blanket_order(
            self.product2,
            10.0,
            "at_confirm",
            company_id=company.id,
            warehouse_id=warehouse.id,
        )
        blanket = blanket.with_context(
            allowed_company_ids=[self.env.company.id, company.id]
        )
        action = blanket.action_deliver_remaining()
        wizard = (
            self.env[action["res_model"]]
            .with_context(allowed_company_ids=[self.env.company.id, company.id])
            .browse(action["res_id"])
        )
        self.assertEqual(wizard.wizard_line_ids.available_qty, 4.0)

    def test_blanket_inherits_replenishment_and_on_order_statuses(self):
        blanket = self._create_blanket_order(self.product2, 10.0, "at_call_off")
        line = blanket.order_line
        self.assertEqual(line.availability_status, "no")
        self.assertEqual(line.delayed_qty, 10.0)
        incoming = self.env["stock.move"].create(
            {
                "name": "Blanket Replenishment",
                "product_id": self.product2.id,
                "product_uom_qty": 10.0,
                "product_uom": self.product2.uom_id.id,
                "picking_type_id": self.wh.in_type_id.id,
                "location_id": self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": self.loc_stock.id,
            }
        )
        line.invalidate_recordset(
            ["availability_status", "expected_availability_date", "delayed_qty"]
        )
        self.assertEqual(line.availability_status, "restock")
        self.assertEqual(line.expected_availability_date, incoming.date)
        self.assertEqual(line.delayed_qty, 10.0)
        with patch.object(type(line), "_on_order_route", return_value=True):
            line.invalidate_recordset(["availability_status", "delayed_qty"])
            self.assertEqual(line.availability_status, "on_order")
            self.assertEqual(line.delayed_qty, 10.0)
