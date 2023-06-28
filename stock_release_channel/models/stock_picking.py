# Copyright 2020 Camptocamp
# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _, exceptions, fields, models

from odoo.addons.queue_job.job import identity_exact


class StockPicking(models.Model):
    _inherit = "stock.picking"

    release_channel_id = fields.Many2one(
        comodel_name="stock.release.channel",
        index=True,
        ondelete="restrict",
        copy=False,
    )
    commercial_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Commercial Entity",
        related="partner_id.commercial_partner_id",
        store=True,
        readonly=True,
    )

    def _delay_assign_release_channel(self):
        for picking in self:
            picking.with_delay(
                identity_key=identity_exact,
                description=_("Assign release channel on %s") % picking.name,
            ).assign_release_channel()

    def assign_release_channel(self):
        for pick in self:
            self.env["stock.release.channel"].assign_release_channel(pick)

    def release_available_to_promise(self):
        for record in self:
            channel = record.release_channel_id
            if channel.release_forbidden:
                raise exceptions.UserError(
                    _(
                        "You cannot release delivery of the channel %s because "
                        "it has been forbidden in the release channel configuration"
                    )
                    % channel.name
                )
        return super().release_available_to_promise()

    def _create_backorder(self):
        backorders = super()._create_backorder()
        backorders._delay_assign_release_channel()
        return backorders

    def assign_release_channel_on_all_need_release(self):
        need_release = self.env["stock.picking"].search(
            [("need_release", "=", True)],
        )
        need_release._delay_assign_release_channel()

    def _find_release_channel_candidate(self):
        """Find a release channel candidate for the picking.

        This method is meant to be overridden in other modules. It allows to
        find a release channel candidate for the current picking based on the
        picking information.

        For example, you could define release channels based on a geographic area.
        In this case, you would need to override this method to find the release
        channel based on the shipping destination. In such a case, it's more
        efficient to search for a channel where the destination is in the channel
        area than to search for all the channels and then filter the ones that match
        the destination as it's done into the method assign_release_channel of the
        stock.release.channel model.

        :return: a release channel or None
        """
        self.ensure_one()
        return None
