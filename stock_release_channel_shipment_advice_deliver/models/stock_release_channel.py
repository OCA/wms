# Copyright 2023 ACSONE SA/NV
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockReleaseChannel(models.Model):
    _inherit = "stock.release.channel"

    state = fields.Selection(
        selection_add=[
            ("delivering", "Delivering"),
            ("delivering_error", "Delivering Error"),
            ("delivered", "Delivered"),
        ],
        help="The state allows you to control the availability of the release channel.\n"
        "* Open: Manual and automatic picking assignment to the release is effective "
        "and release operations are allowed.\n "
        "* Locked: Release operations are forbidden. (Assignement processes are "
        "still working)\n"
        "* Delivering: A background task is running to automatically deliver ready shipments\n"
        "* Delivering Error: An error occurred in the delivery background task\n"
        "* Delivered: Ready transfers are delivered\n"
        "* Asleep: Assigned pickings not processed are unassigned from the release "
        "channel.\n",
    )

    is_action_deliver_allowed = fields.Boolean(
        compute="_compute_is_action_deliver_allowed"
    )
    is_action_delivering_error_allowed = fields.Boolean(
        compute="_compute_is_action_delivering_error_allowed"
    )
    is_action_delivered_allowed = fields.Boolean(
        compute="_compute_is_action_delivered_allowed"
    )
    delivering_error = fields.Text(readonly=True)
    in_process_shipment_advice_ids = fields.One2many(
        "shipment.advice", compute="_compute_in_process_shipment_advice_ids"
    )
    auto_deliver = fields.Boolean()

    @api.depends("shipment_advice_ids")
    def _compute_in_process_shipment_advice_ids(self):
        shipment_advice_model = self.env["shipment.advice"]
        for rec in self:
            rec.in_process_shipment_advice_ids = shipment_advice_model.search(
                [
                    ("in_release_channel_auto_process", "=", True),
                    ("release_channel_id", "=", rec.id),
                ]
            )

    @api.depends("state", "picking_to_plan_ids", "shipment_planning_method")
    def _compute_is_action_deliver_allowed(self):
        for rec in self:
            rec.is_action_deliver_allowed = (
                rec.state
                in (
                    "locked",
                    "delivering_error",
                )
                and bool(rec.picking_to_plan_ids)
                and rec.shipment_planning_method != "none"
                and rec.auto_deliver
            )

    @api.depends("state")
    def _compute_is_action_delivering_error_allowed(self):
        for rec in self:
            rec.is_action_delivering_error_allowed = rec.state == "delivering"

    @api.depends("state")
    def _compute_is_action_delivered_allowed(self):
        for rec in self:
            rec.is_action_delivered_allowed = rec.state == "delivering"

    def _deliver_check_has_picking_planned(self):
        self.ensure_one()
        if not self.picking_to_plan_ids:
            raise UserError(
                _("No picking to deliver for channel %(name)s.", name=self.name)
            )

    def _check_is_action_delivering_error_allowed(self):
        for rec in self:
            if not rec.is_action_delivering_error_allowed:
                raise UserError(
                    _(
                        "Action 'Delivering Error' is not allowed for channel %(name)s.",
                        name=rec.name,
                    )
                )

    def _check_is_action_delivered_allowed(self):
        for rec in self:
            if not rec.is_action_delivered_allowed:
                raise UserError(
                    _(
                        "Action 'Delivered' is not allowed for channel %(name)s.",
                        name=rec.name,
                    )
                )

    def _picking_moves_to_unrelease(self):
        self.ensure_one()
        return self.env["stock.move"].search(
            [
                ("picking_type_id.code", "=", "internal"),
                ("picking_id.release_channel_id", "=", self.id),
                ("state", "not in", ("cancel", "done")),
            ]
        )

    def _shipping_moves_to_unrelease(self):
        moves = self.open_picking_ids.move_ids.filtered(lambda m: m._is_unreleaseable())
        # The internal operation could have been processed without backorder.
        # In this case, we don't have something to unrelease
        for move in moves:
            for internal_moves in move.move_orig_ids._get_chained_moves_iterator(
                "move_orig_ids"
            ):
                if any(im.state not in ("cancel", "done") for im in internal_moves):
                    break
            else:
                moves -= move
        return moves

    def _deliver_cleanup_printed(self):
        """Unset "printed" on non ready transfer

        Otherwise the unrelease will not be allowed
        """
        pickings = self.picking_chain_ids.move_ids.filtered(
            lambda m: m.state in ("confirmed", "partially_available")
            and m.picking_id.state != "assigned"
            and m.picking_id.printed
        ).picking_id
        pickings.printed = False

    def _deliver_check_moves_in_progress(self, moves_to_unrelease) -> None:
        """
        This checks that the moves chain is not in progress (printed or quantity_done)
        """
        iterator = moves_to_unrelease._get_chained_moves_iterator("move_orig_ids")
        next(iterator)  # skip the current move
        for origin_moves in iterator:
            in_progress_moves = origin_moves._in_progress_for_unrelease()
            if in_progress_moves:
                raise UserError(
                    _(
                        "One of the delivery for channel %(name)s is waiting on "
                        "another transfer. \nPlease finish it manually or "
                        "cancel its start and done quantities to be able to deliver.\n"
                        "%(pickings)s",
                        name=self.name,
                        pickings=", ".join(in_progress_moves.mapped("picking_id.name")),
                    )
                )

    def action_deliver(self):
        self.ensure_one()
        if not self.is_action_deliver_allowed:
            raise UserError(
                _(
                    "Action 'Deliver' is not allowed for the channel %(name)s.",
                    name=self.name,
                )
            )
        self._deliver_check_has_picking_planned()
        self._deliver_cleanup_printed()
        moves_to_unrelease = self._shipping_moves_to_unrelease()
        if moves_to_unrelease:
            self._deliver_check_moves_in_progress(moves_to_unrelease)
            if any(not m._is_unreleaseable() for m in moves_to_unrelease):
                raise UserError(
                    _(
                        "Some deliveries have not been prepared but cannot be unreleased."
                        "\n\n%(shipping)s",
                        shipping=", ".join(
                            moves_to_unrelease.picking_id.mapped("name")
                        ),
                    )
                )
            return {
                "name": _("Confirm delivery"),
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "form",
                "res_model": "stock.release.channel.deliver.check.wizard",
                "target": "new",
                "context": {"default_release_channel_id": self.id, **self.env.context},
            }
        self._action_deliver()
        return {}

    def _action_deliver(self):
        self.write({"state": "delivering", "delivering_error": False})
        self.with_delay(
            description=_("Delivering release channel %(name)s.", name=self.name)
        )._process_shipments()

    def action_delivering_error(self):
        self._check_is_action_delivering_error_allowed()
        self.write({"state": "delivering_error"})
        self.env.user.notify_danger(
            message=_(
                "An error occurred in the delivery background task for the channel %(name)s",
                name=self.display_name,
            ),
            title="Delivering Error",
            sticky=True,
        )

    def action_delivered(self):
        self._check_is_action_delivered_allowed()
        self.write({"state": "delivered"})
        # after deliver, we need to unrelease backorders so they can be assigned
        # to release channel later
        self.unrelease_backorders()
        self.env.user.notify_success(
            message=_(
                "The delivery background task is done for the channel %(name)s",
                name=self.display_name,
            ),
            title="Delivering done",
            sticky=True,
        )

    def _process_shipments(self):
        self.ensure_one()
        shipment_advice = self.in_process_shipment_advice_ids.filtered(
            lambda s: s.state in ("in_progress", "error")
        )
        if shipment_advice and len(shipment_advice) == 1:
            shipment_advice.with_delay(
                description=_(
                    "Automatically process the shipment advice %(name)s.",
                    name=shipment_advice.name,
                )
            )._auto_process()
        else:
            self._plan_shipments()

    def action_sleep(self):
        self.in_process_shipment_advice_ids.write(
            {"in_release_channel_auto_process": False}
        )
        return super().action_sleep()

    def _shipment_advice_auto_process_notify_success(self):
        self.ensure_one()
        shipment_states = set(self.in_process_shipment_advice_ids.mapped("state"))
        not_done_states = ["confirmed", "in_progress", "in_process", "error"]
        if any(not_done_state in shipment_states for not_done_state in not_done_states):
            return
        self.action_delivered()

    @api.model
    def _get_delivering_error_message(self, error, related_object):
        return _(
            "An error occurred while processing the delivery automatically:"
            "\n- %(related_object_name)s: %(error)s",
            related_object_name=related_object.display_name,
            error=str(error),
        )

    def _shipment_advice_auto_process_notify_error(self, error_message):
        self.ensure_one()
        if self.state == "delivering_error":
            return
        self.action_delivering_error()
        self.delivering_error = error_message

    @api.depends("state")
    def _compute_is_action_lock_allowed(self):
        res = super()._compute_is_action_lock_allowed()
        for rec in self:
            rec.is_action_lock_allowed = (
                rec.is_action_lock_allowed or rec.state == "delivering_error"
            )
        return res

    @api.depends("state")
    def _compute_is_action_sleep_allowed(self):
        res = super()._compute_is_action_sleep_allowed()
        for rec in self:
            rec.is_action_sleep_allowed = (
                rec.is_action_sleep_allowed or rec.state == "delivered"
            )
        return res

    def unrelease_picking(self):
        shipping_moves_to_unrelease = self._shipping_moves_to_unrelease()
        shipping_moves_to_unrelease.unrelease(safe_unrelease=True)

    def unrelease_backorders(self):
        backorders = (
            self.in_process_shipment_advice_ids.loaded_picking_ids.backorder_ids
        )
        backorders.unrelease(safe_unrelease=True)

    @api.depends("shipment_advice_ids")
    def _compute_shipment_advice_to_print_ids(self):
        res = super()._compute_shipment_advice_to_print_ids()
        for rec in self:
            if rec.auto_deliver:
                rec.shipment_advice_to_print_ids = fields.first(
                    rec.in_process_shipment_advice_ids.filtered(
                        lambda r: r.state == "done"
                    ).sorted("id", reverse=True)
                )
        return res

    @api.model
    def _get_print_shipment_allowed_states(self):
        res = super()._get_print_shipment_allowed_states()
        res.append("delivered")
        return res
