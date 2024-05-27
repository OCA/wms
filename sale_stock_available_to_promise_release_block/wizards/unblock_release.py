# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


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
        default="asap",
        required=True,
    )
    date_deadline = fields.Datetime(
        compute="_compute_date_deadline", store=True, readonly=False, required=True
    )

    _sql_constraints = [
        (
            "check_scheduled_date",
            "CHECK (date_deadline::date >= now()::date)",
            "You cannot reschedule deliveries in the past.",
        ),
    ]

    def _selection_option(self):
        options = [
            ("free", "Free"),
            ("asap", "As soon as possible"),
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
            if rec.option == "asap":
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
        # Update the scheduled date
        date_planned = fields.Datetime.subtract(
            self.date_deadline, days=self.env.company.security_lead
        )
        moves.date = date_planned
        # Re-assign deliveries: moves sharing the same criteria - like date - will
        # be part of the same delivery.
        # NOTE: this will also leverage stock_picking_group_by_partner_by_carrier
        # module if this one is installed for instance
        moves._assign_picking()
        # Unblock release
        moves.action_unblock_release()
        # Clean up empty deliveries
        pickings.filtered(lambda o: not o.move_ids and not o.printed).unlink()
