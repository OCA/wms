# Copyright 2020 Camptocamp
# License OPL-1

from odoo import _, fields, models

from odoo.addons.queue_job.job import identity_exact


class StockPicking(models.Model):
    _inherit = "stock.picking"

    release_channel_id = fields.Many2one(
        comodel_name="stock.release.channel", index=True, ondelete="restrict"
    )

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
