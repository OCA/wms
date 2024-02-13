# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    release_channel_id = fields.Many2one(
        comodel_name="stock.release.channel",
        compute="_compute_release_channel_id",
        store=True,
        readonly=False,
        index=True,
        help=(
            "Specific release channel for the current delivery address based "
            "on expected delivery date."
        ),
        domain=lambda self: self._release_channel_id_domain(),
    )
    release_channel_partner_date_id = fields.Many2one(
        comodel_name="stock.release.channel.partner.date",
        compute="_compute_release_channel_partner_date_id",
    )

    def _release_channel_id_domain(self):
        parts = ", ".join(self._release_channel_id_domain_parts())
        return f"[{parts}]"

    def _release_channel_id_domain_parts(self):
        return [
            "'|', ('warehouse_id', '=', False), ('warehouse_id', '=', warehouse_id)",
        ]

    def _get_release_channel_id_depends(self):
        return ["partner_shipping_id", "warehouse_id", "commitment_date"]

    @api.depends(lambda o: o._get_release_channel_id_depends())
    def _compute_release_channel_id(self):
        for rec in self:
            if not rec._check_release_channel_partner_date_requirements():
                continue
            channel_date = rec.release_channel_partner_date_id
            rec.release_channel_id = channel_date.release_channel_id

    @api.depends(
        "state",
        "partner_shipping_id",
        "commitment_date",
        "expected_date",
        "warehouse_id",
    )
    def _compute_release_channel_partner_date_id(self):
        for rec in self:
            channel_partner_date = rec._get_release_channel_partner_date()
            rec.release_channel_partner_date_id = channel_partner_date

    def _get_release_channel_partner_date(self):
        self.ensure_one()
        model = self.env["stock.release.channel.partner.date"]
        domain = self._get_release_channel_partner_date_domain()
        return domain and model.search(domain, limit=1) or model

    def _get_release_channel_partner_date_domain(self):
        self.ensure_one()
        if not self._check_release_channel_partner_date_requirements():
            return
        delivery_date = self._get_delivery_date()
        return [
            ("release_channel_id.warehouse_id", "in", [False, self.warehouse_id.id]),
            ("partner_id", "=", self.partner_shipping_id.id),
            ("date", "=", delivery_date),
        ]

    def _check_release_channel_partner_date_requirements(self):
        self.ensure_one()
        delivery_date = self._get_delivery_date()
        return delivery_date and self.partner_shipping_id and self.warehouse_id

    def action_confirm(self):
        # Create specific channel entry on order confirmation
        res = super().action_confirm()
        for rec in self:
            rec._create_release_channel_partner_date()
        return res

    def _action_cancel(self):
        # Store specific channel entries before cancelling them as
        # expected_date is unset on cancel orders
        channel_entries = {o.id: o.release_channel_partner_date_id for o in self}
        # Remove specific channel entry when canceling order
        res = super()._action_cancel()
        for rec in self:
            rec._unlink_release_channel_partner_date(
                channel_date=channel_entries[rec.id]
            )
        return res

    def _create_release_channel_partner_date(self):
        self.ensure_one()
        model = self.env["stock.release.channel.partner.date"]
        if self.state not in ("sale", "done") or not self.release_channel_id:
            return model
        channel = self.release_channel_id.with_context(active_test=False)
        channel_dates = channel.release_channel_partner_date_ids.filtered_domain(
            self._get_release_channel_partner_date_domain()
        )
        if channel_dates:
            channel_dates.write({"active": True})
        else:
            values = self._prepare_release_channel_partner_date_values()
            return model.create(values)
        return model

    def _prepare_release_channel_partner_date_values(self):
        self.ensure_one()
        delivery_date = self._get_delivery_date()
        assert delivery_date
        return {
            "release_channel_id": self.release_channel_id.id,
            "partner_id": self.partner_shipping_id.id,
            "date": delivery_date,
        }

    def _unlink_release_channel_partner_date(self, channel_date):
        self.ensure_one()
        if self.state != "cancel":
            return False
        # Check if specific channel entry is used by another order
        if channel_date:
            domain = self._unlink_release_channel_partner_date_domain(channel_date)
            other_orders = self.search(domain)
            other_orders = other_orders.filtered(
                lambda o: o._get_delivery_date() == channel_date.date
            )
            if not other_orders:
                channel_date.unlink()
        return False

    def _unlink_release_channel_partner_date_domain(self, channel_date):
        return [
            ("id", "!=", self.id),
            ("state", "in", ("draft", "sent", "sale", "done")),
            ("delivery_status", "!=", "full"),
            ("release_channel_id", "=", channel_date.release_channel_id.id),
            ("partner_shipping_id", "=", channel_date.partner_id.id),
        ]

    def _get_delivery_date(self):
        self.ensure_one()
        date = self.commitment_date or self.expected_date
        tz = (
            self.sudo().warehouse_id.partner_id.tz
            or self.env.company.partner_id.tz
            or "UTC"
        )
        return (
            date
            and fields.Datetime.context_timestamp(
                self.with_context(tz=tz),
                date,
            ).date()
        )
