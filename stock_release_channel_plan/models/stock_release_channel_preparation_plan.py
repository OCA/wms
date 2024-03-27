# Copyright 2023 ACSONE SA/NV
# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockReleaseChannelPreparationPlan(models.Model):
    _name = "stock.release.channel.preparation.plan"
    _description = "Stock Release Channel Preparation Plan"
    _order = "sequence, id"

    sequence = fields.Integer()
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    release_channel_ids = fields.Many2many(
        comodel_name="stock.release.channel",
        relation="stock_release_channel_preparation_plan_rel",
        column1="plan_id",
        column2="channel_id",
        string="Release channels",
    )

    def _get_channels_to_launch_domain(self):
        self.ensure_one()
        return [
            ("state", "in", ("locked", "asleep")),
        ]

    def _get_channels_to_launch(self):
        return self.release_channel_ids.filtered_domain(
            self._get_channels_to_launch_domain()
        )
