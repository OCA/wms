# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import _, api, exceptions, fields, models


class UnblockRelease(models.TransientModel):
    _name = "unblock.release"
    _description = "Unblock Release"

    order_line_ids = fields.Many2many(
        comodel_name="sale.order.line",
        string="Order Lines",
        readonly=True,
    )
    move_ids = fields.Many2many(
        comodel_name="stock.move",
        string="Delivery moves",
        readonly=True,
    )
    option = fields.Selection(
        selection=lambda self: self._selection_option(),
        default="automatic",
        required=True,
        help=(
            "- Manual: schedule blocked deliveries at a given date;\n"
            "- Automatic: schedule blocked deliveries as soon as possible;\n"
            "- Based on current order: schedule blocked deliveries with the "
            "contextual sale order."
        ),
    )
    order_id = fields.Many2one(comodel_name="sale.order", string="Order", readonly=True)
    date_deadline = fields.Datetime(
        compute="_compute_date_deadline", store=True, readonly=False, required=True
    )

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
            options.append(("contextual", "Based on current order"))
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
        if from_sale_order:
            res["order_id"] = from_sale_order_id
        if active_model == "sale.order.line" and active_ids:
            res["order_line_ids"] = [(6, 0, active_ids)]
        if active_model == "stock.move" and active_ids:
            res["move_ids"] = [(6, 0, active_ids)]
        if from_sale_order:
            res["option"] = "contextual"
        return res

    def validate(self):
        self.ensure_one()
        moves = self._filter_moves(self.order_line_ids.move_ids or self.move_ids)
        if self.option == "contextual":
            self._plan_moves_for_current_order(moves)
        else:
            self._reschedule_moves(moves, self.date_deadline)
            # Unblock release
            moves.action_unblock_release()

    def _filter_moves(self, moves):
        return moves.filtered_domain(
            [("state", "=", "waiting"), ("release_blocked", "=", True)]
        )

    def _plan_moves_for_current_order(self, moves):
        """Plan moves to be unblocked when the current order is confirmed."""
        self.order_id.move_to_unblock_ids = moves

    @api.model
    def _reschedule_moves(self, moves, date_deadline, from_order=None):
        """Reschedule the moves based on the deadline."""
        # Filter out moves that don't need to be released
        moves = moves.filtered("need_release")
        # Unset current deliveries (keep track of them to delete empty ones at the end)
        pickings = moves.picking_id
        moves.picking_id = False
        # If the rescheduling is triggered from a sale order we set a dedicated
        # procurement group on blocked moves.
        # This has the side-effect to benefit from other modules like
        # 'stock_picking_group_by_partner_by_carrier*' to get existing moves
        # and new ones merged together if they share the same criteria
        # (picking policy, carrier, scheduled date...).
        if from_order:
            group = self.env["procurement.group"].create(
                fields.first(from_order.order_line)._prepare_procurement_group_vals()
            )
            group.name += " BACKORDERS"
            moves.group_id = group
        # Update the scheduled date and date deadline
        date_planned = fields.Datetime.subtract(
            date_deadline, days=self.env.company.security_lead
        )
        moves.date = date_planned
        moves.date_deadline = date_deadline
        # Re-assign deliveries
        moves._assign_picking()
        # Clean up empty deliveries
        pickings.filtered(lambda o: not o.move_ids and not o.printed).unlink()
