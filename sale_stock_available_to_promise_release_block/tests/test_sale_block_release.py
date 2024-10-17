# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import exceptions, fields
from odoo.tests.common import Form

from odoo.addons.sale_stock_available_to_promise_release.tests import common


class TestSaleBlockRelease(common.Common):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Ensure there is no security lead during tests
        cls.env.company.security_lead = 0
        # Deliver in two steps to get a SHIP to release
        cls.wh = cls.env.ref("stock.warehouse0")
        cls.wh.delivery_steps = "pick_ship"
        cls.wh.delivery_route_id.available_to_promise_defer_pull = True

    def test_sale_release_not_blocked(self):
        self._set_stock(self.line.product_id, self.line.product_uom_qty)
        self.assertFalse(self.sale.block_release)
        self.sale.action_confirm()
        self.assertFalse(self.sale.picking_ids.release_blocked)

    def test_sale_release_blocked(self):
        self._set_stock(self.line.product_id, self.line.product_uom_qty)
        self.sale.block_release = True
        self.sale.action_confirm()
        self.assertTrue(self.sale.picking_ids.release_blocked)

    def _create_unblock_release_wizard(
        self, records=None, date_deadline=None, from_order=None, option="manual"
    ):
        wiz_form = Form(
            self.env["unblock.release"].with_context(
                from_sale_order_id=from_order and from_order.id,
                active_model=records._name,
                active_ids=records.ids,
                default_option=option,
            )
        )
        if date_deadline:
            wiz_form.date_deadline = date_deadline
        return wiz_form.save()

    def test_unblock_release_contextual(self):
        self._set_stock(self.line.product_id, self.line.product_uom_qty)
        self.sale.block_release = True
        self.sale.action_confirm()
        existing_moves = self.sale.order_line.move_ids
        # Unblock deliveries through the wizard, opened from another SO
        new_sale = self._create_sale_order()
        self.env["sale.order.line"].create(
            {
                "order_id": new_sale.id,
                "product_id": self.product.id,
                "product_uom_qty": 50,
                "product_uom": self.uom_unit.id,
            }
        )
        new_sale.commitment_date = fields.Datetime.add(fields.Datetime.now(), days=1)
        self.assertIn(existing_moves, new_sale.available_move_to_unblock_ids)
        wiz = self._create_unblock_release_wizard(
            self.sale.order_line, from_order=new_sale
        )
        self.assertEqual(wiz.option, "contextual")
        self.assertEqual(wiz.order_id, new_sale)
        self.assertEqual(wiz.date_deadline, new_sale.commitment_date)
        self.assertNotEqual(wiz.order_line_ids.move_ids.date, new_sale.commitment_date)
        old_picking = wiz.order_line_ids.move_ids.picking_id
        wiz.validate()
        # Deliveries will be unblocked when the new SO is confirmed
        self.assertFalse(new_sale.available_move_to_unblock_ids)
        self.assertEqual(new_sale.move_to_unblock_ids, existing_moves)
        # Confirm the new SO: deliveries have been scheduled to the new date deadline
        new_sale.action_confirm()
        new_moves = new_sale.order_line.move_ids
        new_picking = wiz.order_line_ids.move_ids.picking_id
        self.assertNotEqual(old_picking, new_picking)
        self.assertFalse(old_picking.exists())
        self.assertTrue(
            all(
                m.date == m.date_deadline == new_sale.commitment_date
                for m in (existing_moves | new_moves)
            )
        )
        self.assertTrue(
            all(not m.release_blocked for m in (existing_moves | new_moves))
        )

    def test_unblock_release_contextual_order_not_eligible(self):
        self._set_stock(self.line.product_id, self.line.product_uom_qty)
        self.sale.block_release = True
        self.sale.action_confirm()
        # Unblock deliveries through the wizard, opened from another SO
        new_sale = self._create_sale_order()
        self.env["sale.order.line"].create(
            {
                "order_id": new_sale.id,
                "product_id": self.product.id,
                "product_uom_qty": 50,
                "product_uom": self.uom_unit.id,
            }
        )
        new_sale.action_cancel()
        wiz = self._create_unblock_release_wizard(
            self.sale.order_line,
            from_order=new_sale,
            date_deadline=fields.Datetime.now(),
        )
        self.assertEqual(wiz.option, "manual")

    def test_unblock_release_contextual_different_shipping_policy(self):
        self._set_stock(self.line.product_id, self.line.product_uom_qty)
        self.sale.block_release = True
        self.sale.action_confirm()
        existing_moves = self.sale.order_line.move_ids
        # Unblock deliveries through the wizard, opened from another SO with a
        # different shipping_policy
        new_sale = self._create_sale_order()
        new_sale.picking_policy = "one"
        self.env["sale.order.line"].create(
            {
                "order_id": new_sale.id,
                "product_id": self.product.id,
                "product_uom_qty": 50,
                "product_uom": self.uom_unit.id,
            }
        )
        new_sale.commitment_date = fields.Datetime.add(fields.Datetime.now(), days=1)
        self.assertIn(existing_moves, new_sale.available_move_to_unblock_ids)
        wiz = self._create_unblock_release_wizard(
            self.sale.order_line, from_order=new_sale
        )
        self.assertEqual(wiz.option, "contextual")
        self.assertEqual(wiz.order_id, new_sale)
        self.assertEqual(wiz.date_deadline, new_sale.commitment_date)
        self.assertNotEqual(wiz.order_line_ids.move_ids.date, new_sale.commitment_date)
        self.assertNotEqual(
            wiz.order_line_ids.move_ids.group_id.move_type, new_sale.picking_policy
        )
        old_picking = wiz.order_line_ids.move_ids.picking_id
        wiz.validate()
        # Deliveries will be unblocked when the new SO is confirmed
        self.assertFalse(new_sale.available_move_to_unblock_ids)
        self.assertEqual(new_sale.move_to_unblock_ids, existing_moves)
        # Confirm the new SO: deliveries have been scheduled to the new date deadline
        # with the same shipping policy
        new_sale.action_confirm()
        new_moves = new_sale.order_line.move_ids
        new_picking = wiz.order_line_ids.move_ids.picking_id
        self.assertNotEqual(old_picking, new_picking)
        self.assertFalse(old_picking.exists())
        self.assertTrue(
            all(
                m.date == m.date_deadline == new_sale.commitment_date
                for m in (existing_moves | new_moves)
            )
        )
        self.assertTrue(
            all(not m.release_blocked for m in (existing_moves | new_moves))
        )
        self.assertEqual(
            existing_moves.group_id.move_type, new_moves.group_id.move_type
        )

    def test_unblock_release_manual(self):
        self._set_stock(self.line.product_id, self.line.product_uom_qty)
        self.sale.block_release = True
        self.sale.action_confirm()
        # Unblock deliveries through the wizard
        new_date_deadline = fields.Datetime.add(fields.Datetime.now(), days=1)
        wiz = self._create_unblock_release_wizard(
            self.sale.order_line, date_deadline=new_date_deadline
        )
        self.assertEqual(wiz.option, "manual")
        self.assertEqual(wiz.date_deadline, new_date_deadline)
        self.assertNotEqual(wiz.order_line_ids.move_ids.date, new_date_deadline)
        old_picking = wiz.order_line_ids.move_ids.picking_id
        wiz.validate()
        # Deliveries have been scheduled to the new date deadline
        new_picking = wiz.order_line_ids.move_ids.picking_id
        self.assertEqual(wiz.order_line_ids.move_ids.date, new_date_deadline)
        self.assertNotEqual(old_picking, new_picking)
        self.assertFalse(old_picking.exists())

    def test_unblock_release_automatic(self):
        # Start with a blocked SO having a commitment date in the past
        self._set_stock(self.line.product_id, self.line.product_uom_qty)
        self.sale.block_release = True
        yesterday = fields.Datetime.subtract(fields.Datetime.now(), days=1)
        self.sale.commitment_date = yesterday
        self.sale.action_confirm()
        # Unblock deliveries through the wizard
        wiz = self._create_unblock_release_wizard(
            self.sale.order_line, option="automatic"
        )
        today = wiz.date_deadline
        self.assertEqual(wiz.option, "automatic")
        self.assertEqual(wiz.date_deadline, today)
        self.assertNotEqual(wiz.order_line_ids.move_ids.date, today)
        old_picking = wiz.order_line_ids.move_ids.picking_id
        wiz.validate()
        # Deliveries have been scheduled for today
        new_picking = wiz.order_line_ids.move_ids.picking_id
        self.assertEqual(wiz.order_line_ids.move_ids.date, today)
        self.assertNotEqual(old_picking, new_picking)
        self.assertFalse(old_picking.exists())

    def test_unblock_release_automatic_from_moves(self):
        # Same test than above but running the wizard from moves.
        # Start with a blocked SO having a commitment date in the past
        self._set_stock(self.line.product_id, self.line.product_uom_qty)
        self.sale.block_release = True
        yesterday = fields.Datetime.subtract(fields.Datetime.now(), days=1)
        self.sale.commitment_date = yesterday
        self.sale.action_confirm()
        # Unblock deliveries through the wizard
        today = fields.Datetime.now()
        wiz = self._create_unblock_release_wizard(
            self.sale.order_line.move_ids, option="automatic"
        )
        self.assertEqual(wiz.date_deadline, today)
        self.assertNotEqual(wiz.move_ids.date, today)
        old_picking = wiz.move_ids.picking_id
        wiz.validate()
        # Deliveries have been scheduled for today
        new_picking = wiz.move_ids.picking_id
        self.assertEqual(wiz.move_ids.date, today)
        self.assertNotEqual(old_picking, new_picking)
        self.assertFalse(old_picking.exists())

    def test_unblock_release_past_date_deadline(self):
        self._set_stock(self.line.product_id, self.line.product_uom_qty)
        self.sale.block_release = True
        self.sale.action_confirm()
        # Try to unblock deliveries through the wizard with a scheduled date
        # in the past
        yesterday = fields.Datetime.subtract(fields.Datetime.now(), days=1)
        with self.assertRaises(exceptions.ValidationError):
            self._create_unblock_release_wizard(
                self.sale.order_line, date_deadline=yesterday
            )
