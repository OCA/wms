# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import psycopg2

from odoo import fields
from odoo.tests.common import Form

from odoo.addons.sale_stock_available_to_promise_release.tests import common


class TestSaleBlockRelease(common.Common):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Ensure there is no security lead during tests
        cls.env.company.security_lead = 0

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
        self, order_lines, date_deadline=None, from_order=None, option="free"
    ):
        wiz_form = Form(
            self.env["unblock.release"].with_context(
                from_sale_order_id=from_order and from_order.id,
                active_model=order_lines._name,
                active_ids=order_lines.ids,
                default_option=option,
            )
        )
        if date_deadline:
            wiz_form.date_deadline = date_deadline
        return wiz_form.save()

    def test_sale_order_line_unblock_release_contextual(self):
        self._set_stock(self.line.product_id, self.line.product_uom_qty)
        self.sale.block_release = True
        self.sale.action_confirm()
        # Unblock deliveries through the wizard, opened from another SO
        # to define default values
        new_sale = self._create_sale_order()
        new_sale.commitment_date = fields.Datetime.add(fields.Datetime.now(), days=1)
        wiz = self._create_unblock_release_wizard(
            self.sale.order_line, from_order=new_sale
        )
        self.assertEqual(wiz.option, "contextual")
        self.assertEqual(wiz.date_deadline, new_sale.commitment_date)
        self.assertNotEqual(wiz.order_line_ids.move_ids.date, new_sale.commitment_date)
        old_picking = wiz.order_line_ids.move_ids.picking_id
        wiz.validate()
        # Deliveries have been scheduled to the new date deadline
        new_picking = wiz.order_line_ids.move_ids.picking_id
        self.assertEqual(wiz.order_line_ids.move_ids.date, new_sale.commitment_date)
        self.assertNotEqual(old_picking, new_picking)
        self.assertFalse(old_picking.exists())

    def test_sale_order_line_unblock_release_free(self):
        self._set_stock(self.line.product_id, self.line.product_uom_qty)
        self.sale.block_release = True
        self.sale.action_confirm()
        # Unblock deliveries through the wizard
        new_date_deadline = fields.Datetime.add(fields.Datetime.now(), days=1)
        wiz = self._create_unblock_release_wizard(
            self.sale.order_line, date_deadline=new_date_deadline
        )
        self.assertEqual(wiz.date_deadline, new_date_deadline)
        self.assertNotEqual(wiz.order_line_ids.move_ids.date, new_date_deadline)
        old_picking = wiz.order_line_ids.move_ids.picking_id
        wiz.validate()
        # Deliveries have been scheduled to the new date deadline
        new_picking = wiz.order_line_ids.move_ids.picking_id
        self.assertEqual(wiz.order_line_ids.move_ids.date, new_date_deadline)
        self.assertNotEqual(old_picking, new_picking)
        self.assertFalse(old_picking.exists())

    def test_sale_order_line_unblock_release_asap(self):
        # Start with a blocked SO having a commitment date in the past
        self._set_stock(self.line.product_id, self.line.product_uom_qty)
        self.sale.block_release = True
        yesterday = fields.Datetime.subtract(fields.Datetime.now(), days=1)
        self.sale.commitment_date = yesterday
        self.sale.action_confirm()
        # Unblock deliveries through the wizard
        today = fields.Datetime.now()
        wiz = self._create_unblock_release_wizard(self.sale.order_line, option="asap")
        self.assertEqual(wiz.date_deadline, today)
        self.assertNotEqual(wiz.order_line_ids.move_ids.date, today)
        old_picking = wiz.order_line_ids.move_ids.picking_id
        wiz.validate()
        # Deliveries have been scheduled for today
        new_picking = wiz.order_line_ids.move_ids.picking_id
        self.assertEqual(wiz.order_line_ids.move_ids.date, today)
        self.assertNotEqual(old_picking, new_picking)
        self.assertFalse(old_picking.exists())

    def test_sale_order_line_unblock_release_past_date_deadline(self):
        self._set_stock(self.line.product_id, self.line.product_uom_qty)
        self.sale.block_release = True
        self.sale.action_confirm()
        # Try to unblock deliveries through the wizard with a scheduled date
        # in the past
        new_sale = self._create_sale_order()
        yesterday = fields.Datetime.subtract(fields.Datetime.now(), days=1)
        with self.assertRaises(psycopg2.errors.CheckViolation):
            self._create_unblock_release_wizard(
                self.sale.order_line, date_deadline=yesterday, from_order=new_sale
            )
