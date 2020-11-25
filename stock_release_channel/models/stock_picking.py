# Copyright 2020 Camptocamp
# License OPL-1

from odoo import _, api, fields, models

from odoo.addons.queue_job.job import identity_exact


class StockPicking(models.Model):
    _inherit = "stock.picking"

    release_channel_id = fields.Many2one(
        comodel_name="stock.release.channel",
        # we have to store it on stock.move, because when (for e.g.)
        # a dynamic routing put moves in another picking (_assign_picking),
        # we want the new one to keep this information
        compute="_compute_release_channel_id",
        inverse="_inverse_release_channel_id",
        index=True,
        store=True,
    )

    @api.depends("move_lines.release_channel_id")
    def _compute_release_channel_id(self):
        for picking in self:
            picking.release_channel_id = fields.first(
                picking.move_lines.release_channel_id
            )

    def _inverse_release_channel_id(self):
        for picking in self:
            picking.move_lines.write({"release_channel_id": picking.release_channel_id})

    def _delay_assign_release_channel(self):
        for picking in self:
            picking.with_delay(
                identity_key=identity_exact,
                description=_("Assign release channel on {}").format(picking.name),
            ).assign_release_channel()

    def assign_release_channel(self):
        self.env["stock.release.channel"].assign_release_channel(self)

    def _create_backorder(self):
        backorders = super()._create_backorder()
        backorders._delay_assign_release_channel()
        return backorders

    def assign_release_channel_on_all_need_release(self):
        need_release = self.env["stock.picking"].search([("need_release", "=", True)],)
        need_release._delay_assign_release_channel()
