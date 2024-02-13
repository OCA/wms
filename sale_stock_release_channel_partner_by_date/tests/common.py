# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests.common import Form

from odoo.addons.stock_release_channel.tests.common import ReleaseChannelCase


class SaleReleaseChannelCase(ReleaseChannelCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.groups_id |= cls.env.ref("account.group_delivery_invoice_address")
        cls.customer = cls.env.ref("base.res_partner_1")
        cls.default_channel.sequence = 1
        cls.test_channel = cls.default_channel.copy({"name": "Test", "sequence": 10})
        cls.test_channel.action_wake_up()

    @classmethod
    def _create_sale_order(cls, channel=False, date=False, warehouse=False):
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.customer
        if warehouse:
            sale_form.warehouse_id = warehouse
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product
            line_form.product_uom_qty = 1
        if date:
            sale_form.commitment_date = date
        # Set a specific channel after lines to get an expected_date
        if channel:
            sale_form.release_channel_id = channel
        return sale_form.save()
