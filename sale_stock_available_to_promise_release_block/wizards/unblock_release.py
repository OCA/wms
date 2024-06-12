# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import _, api, exceptions, fields, models


class UnblockRelease(models.TransientModel):
    _name = "unblock.release"
    _description = "Unblock Release"

    order_line_ids = fields.Many2many(
        comodel_name="sale.order.line",
        string="Order Lines",
    )
    move_ids = fields.Many2many(
        comodel_name="stock.move",
        string="Delivery moves",
    )
    option = fields.Selection(
        selection=lambda self: self._selection_option(),
        default="automatic",
        required=True,
        help=(
            "- Manual: schedule blocked deliveries at a given date;\n"
            "- Automatic: schedule blocked deliveries as soon as possible;\n"
            "- Contextual: schedule blocked deliveries based by default on the "
            "commitment date of the contextual sale order. Commitment date of "
            "the order will be updated if not yet confirmed.",
        ),
        # help=(
        #     "- Manual: schedule blocked deliveries at a given date, in the "
        #     "chosen release channel;\n"
        #     "- Automatic: schedule blocked deliveries as soon as possible in the "
        #     "relevant release channel;\n"
        #     "- Contextual: schedule blocked deliveries based by default on the "
        #     "commitment date and release channel (if any) of the contextual "
        #     "sale order. Commitment date and release channel of the order will "
        #     "be updated if not yet confirmed.\n",
        # ),
    )
    date_deadline = fields.Datetime(
        compute="_compute_date_deadline", store=True, readonly=False, required=True
    )
    # release_channel_id = fields.Many2one("stock.release.channel", required=True)

    @api.constrains("date_deadline")
    def _constrains_date_deadline(self):
        today = fields.Date.today()
        for rec in self:
            if rec.date_deadline.date() < today:
                raise exceptions.ValidationError(
                    _("You cannot reschedule deliveries in the past.")
                )

    def _selection_option(self):
        options = [
            ("manual", "Manual"),
            ("automatic", "Automatic / As soon as possible"),
        ]
        if self.env.context.get("from_sale_order_id"):
            options.append(("contextual", "From contextual sale order"))
        return options

    @api.depends("option")
    def _compute_date_deadline(self):
        from_sale_order_id = self.env.context.get("from_sale_order_id")
        order = self.env["sale.order"].browse(from_sale_order_id).exists()
        for rec in self:
            rec.date_deadline = False
            if rec.option == "automatic":
                rec.date_deadline = fields.Datetime.now()
            elif rec.option == "contextual" and order:
                rec.date_deadline = order.commitment_date or order.expected_date

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids")
        from_sale_order_id = self.env.context.get("from_sale_order_id")
        from_sale_order = self.env["sale.order"].browse(from_sale_order_id).exists()
        if active_model == "sale.order.line" and active_ids:
            res["order_line_ids"] = [(6, 0, active_ids)]
        if active_model == "stock.move" and active_ids:
            res["move_ids"] = [(6, 0, active_ids)]
        if from_sale_order:
            res["option"] = "contextual"
        return res

    def validate(self):
        self.ensure_one()
        move_states = (
            "draft",
            "waiting",
            "confirmed",
            "partially_available",
            "assigned",
        )
        moves = (self.order_line_ids.move_ids or self.move_ids).filtered_domain(
            [("state", "in", move_states), ("release_blocked", "=", True)]
        )
        # Unset current deliveries (keep track of them to delete empty ones at the end)
        pickings = moves.picking_id
        moves.picking_id = False
        # Update the scheduled date and date deadline
        date_planned = fields.Datetime.subtract(
            self.date_deadline, days=self.env.company.security_lead
        )
        moves.date = date_planned
        moves.date_deadline = self.date_deadline
        # Re-assign deliveries: moves sharing the same criteria - like date - will
        # be part of the same delivery.
        # NOTE: this will also leverage stock_picking_group_by_partner_by_carrier
        # module if this one is installed for instance
        moves._assign_picking()
        # Unblock release
        moves.action_unblock_release()
        # Clean up empty deliveries
        pickings.filtered(lambda o: not o.move_ids and not o.printed).unlink()
        # Update commitment date of contextual sale order if any
        from_sale_order_id = self.env.context.get("from_sale_order_id")
        from_sale_order = self.env["sale.order"].browse(from_sale_order_id).exists()
        if from_sale_order.state in ("draft", "sent"):
            from_sale_order.commitment_date = self.date_deadline
