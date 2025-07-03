# Copyright 2024 Camptocamp SA
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools import ormcache

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends(
        "order_line.customer_lead",
        "date_order",
        "partner_shipping_id",
        "carrier_id",
        "warehouse_id",
        "picking_policy",
    )
    def _compute_expected_date(self):
        res = super()._compute_expected_date()
        for order in self:
            if not order.partner_shipping_id:
                # do not recompute
                continue
            if order.order_line:
                # will be managed at line level
                continue
            if order.state in ["sale", "done"] and order.date_order:
                order_dt = order.date_order
            else:
                order_dt = fields.Datetime.now()

            order.expected_date = order._get_release_channel_expected_date(order_dt)
        return res

    def _get_release_channel_expected_date(self, order_dt):
        self.ensure_one()
        # If the carrier is not set, assume the partner default carrier
        carrier = (
            self.carrier_id or self.partner_shipping_id.property_delivery_carrier_id
        )
        # We don't need that precision for the computation & cache
        order_dt = order_dt.replace(second=0, microsecond=0)
        expected_dt = self._cached_release_channel_expected_date(carrier, order_dt)
        return expected_dt

    @ormcache(
        "self.company_id.id",
        "self.partner_shipping_id.id",
        "self.warehouse_id.id",
        "carrier.id",
        "order_dt",
    )
    def _cached_release_channel_expected_date(self, carrier, order_dt):
        self.ensure_one()
        _logger.debug(f"Computing expected date for {self} starting from {order_dt}")

        channels = self._get_partner_release_channels(carrier)
        if not channels:
            return False
        dates = [
            channel._get_earliest_delivery_date(self.partner_shipping_id, order_dt)
            for channel in channels
        ]
        return min(dates)

    @api.model
    def _get_partner_release_channels(self, carrier):
        domain_order = self._release_channel_possible_candidate_domain_base
        domain_partner = (
            self.partner_shipping_id._release_channel_possible_candidate_domain
            if self.partner_shipping_id
            else []
        )
        domain_channel = [("is_manual_assignment", "=", False)]
        domain = expression.AND([domain_order, domain_partner, domain_channel])
        return self.env["stock.release.channel"].search(domain)
