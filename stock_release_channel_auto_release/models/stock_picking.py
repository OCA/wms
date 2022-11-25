# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.osv.expression import AND

from odoo.addons.queue_job.job import identity_exact


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @api.model
    def _is_auto_release_allowed_depends(self):
        depends = super()._is_auto_release_allowed_depends()
        depends.append("release_channel_id.is_auto_release_allowed")
        return depends

    @property
    def _is_auto_release_allowed_domain(self):
        domain = super()._is_auto_release_allowed_domain
        return AND(
            [
                domain,
                [("release_channel_id.is_auto_release_allowed", "=", True)],
            ]
        )

    def _delay_auto_release_available_to_promise(self):
        for picking in self:
            picking.with_delay(
                identity_key=identity_exact,
                description=_(
                    "Auto release available to promise %(name)s", name=picking.name
                ),
            ).auto_release_available_to_promise()

    def auto_release_available_to_promise(self):
        to_release = self.filtered("is_auto_release_allowed")
        to_release.release_available_to_promise()
        return to_release

    def assign_release_channel(self):
        res = super().assign_release_channel()
        self.filtered(
            "is_auto_release_allowed"
        )._delay_auto_release_available_to_promise()
        return res
