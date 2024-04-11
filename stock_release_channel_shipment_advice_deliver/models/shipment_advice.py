# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ShipmentAdvice(models.Model):
    _inherit = "shipment.advice"

    in_release_channel_auto_process = fields.Boolean(
        readonly=True,
        help="Technical field to flag shipment advice that are in a release channel "
        "auto-process",
        index=True,
    )

    @property
    def _is_auto_process(self) -> bool:
        """We consider that a shipment advice created for a release channel in 'delivering'.

        state should be processed automatically
        In this way we avoid that the release channel keep watching the shipment advice
        creation and process them. Each shipment advice manage its own process and call
        the release channel to notify it when it's done.
        """
        return self.release_channel_id and self.release_channel_id.state in (
            "delivering",
            "delivering_error",
        )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec._is_auto_process:
                rec.with_delay(
                    description=_(
                        "Automatically process the shipment advice %(name)s.",
                        name=rec.name,
                    )
                )._auto_process()
        return records

    def _auto_process(self):
        self.ensure_one()
        if not self._is_auto_process:
            return False
        if not self.arrival_date:
            self.arrival_date = fields.Date.context_today(self)
        self.in_release_channel_auto_process = True
        try:
            with self.env.cr.savepoint():
                move_lines = self.planned_move_ids.move_line_ids
                move_lines_to_load = move_lines.filtered(
                    lambda ml: ml.state not in ("done", "cancel")
                )
                move_lines_to_load._load_in_shipment(self)
                if self.state == "confirmed":
                    self.action_in_progress()
                self.action_done()
        except UserError as error:
            _logger.error(error)
            self.write(
                {
                    "state": "error",
                    "error_message": self._get_error_message(error, self),
                }
            )
            self.release_channel_id._shipment_advice_auto_process_notify_error(
                self.error_message
            )
        return True

    def _postprocess_action_done(self):
        res = super()._postprocess_action_done()
        if self.state == "error":
            return self.release_channel_id._shipment_advice_auto_process_notify_error(
                self.error_message
            )
        if self.state != "done":
            return res
        return self.release_channel_id._shipment_advice_auto_process_notify_success()

    def action_done(self):
        # If the channel is in error and we try to validate its shipment
        # advice, we set the release channel state to delivering."""
        for rec in self:
            if (
                rec.state == "error"
                and rec.release_channel_id
                and rec.release_channel_id.state == "delivering_error"
            ):
                rec.release_channel_id.state = "delivering"
        return super().action_done()

    def action_in_progress(self):
        res = super().action_in_progress()
        self.release_channel_id.filtered(
            "is_action_deliver_allowed"
        ).state = "delivering"
        return res
