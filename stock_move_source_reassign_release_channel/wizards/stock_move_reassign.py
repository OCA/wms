# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.osv.expression import AND
from odoo.tools import ValidationError


class StockMoveReassign(models.TransientModel):

    _inherit = "stock.move.reassign"

    release_channel_id = fields.Many2one(
        comodel_name="stock.release.channel",
        ondelete="cascade",
    )
    release_channel_id_domain = fields.Binary(
        compute="_compute_release_channel_id_domain"
    )

    @api.depends("release_channel_id")
    def _compute_destination_picking_domain(self):
        res = super()._compute_destination_picking_domain()
        for record in self:
            if record.release_channel_id:
                record.destination_picking_domain = AND(
                    [
                        record.destination_picking_domain,
                        [("release_channel_id", "=", record.release_channel_id.id)],
                    ]
                )

        return res

    @api.depends("move_ids")
    def _compute_release_channel_id_domain(self):
        for record in self:
            record.release_channel_id_domain = [("state", "in", ("open", "locked"))]

    def _get_reassign_extra_values(self):
        res = super()._get_reassign_extra_values()
        if self.release_channel_id:
            res["reassign_release_channel_id"] = self.release_channel_id.id
        return res

    def _check_release_channel(self):
        self.ensure_one()
        if self.step == "ask_picking_type":
            if self.release_channel_id and not self.release_channel_id.filtered_domain(
                self.release_channel_id_domain
            ):
                raise ValidationError(
                    _(
                        "You cannot use the release channel %(name)s as it "
                        "is not in a correct state!",
                        name=self.release_channel_id.name,
                    )
                )

    def doit(self):
        for wizard in self:
            wizard._check_release_channel()
        return super().doit()
