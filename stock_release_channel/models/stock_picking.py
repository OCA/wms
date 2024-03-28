# Copyright 2020 Camptocamp
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
        tracking=True,
        inverse="_inverse_release_channel_id",
    )

    def _inverse_release_channel_id(self):
        """When the release channel is modified, update the expected date

        Set new date on all moves in the chain"""
        for delivery in self:
            if not delivery.last_release_date:
                continue
            if delivery.picking_type_code != "outgoing":
                continue
            channel = delivery.release_channel_id
            new_date = channel and channel._get_expected_date()
            if not new_date:
                continue
            moves = delivery.move_ids.filtered(
                lambda m: m.state not in ("cancel", "done")
            )
            move_chain_ids = []
            while moves:
                move_chain_ids += moves.ids
                moves = moves.move_orig_ids.filtered(
                    lambda m: m.state not in ("cancel", "done")
                )
            all_moves = moves.browse(move_chain_ids)
            all_moves._release_set_expected_date(new_date)

    def _delay_assign_release_channel(self):
        for picking in self:
            picking.with_delay(
                identity_key=identity_exact,
                description=_("Assign release channel on %s") % picking.name,
            ).assign_release_channel()

    def assign_release_channel(self):
        messages = ""
        for pick in self:
            result = self.env["stock.release.channel"].assign_release_channel(pick)
            if result:
                messages += result + "\n"
        return messages

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

    def _find_release_channel_possible_candidate(self):
        """Find release channels possible candidate for the picking.

        This method is meant to be inherited in other modules to add more criteria of
        channel selection. It allows to find all possible channels for the current
        picking(s) based on the picking information.

        For example, you could define release channels based on a geographic area.
        In this case, you would need to override this method to find the release
        channel based on the shipping destination. In such a case, it's more
        efficient to search for a channel where the destination is in the channel
        area than to search for all the channels and then filter the ones that match
        the destination as it's done into the method assign_release_channel of the
        stock.release.channel model.

        :return: release channels
        """
        self.ensure_one()
        return (
            self.env["stock.release.channel"]
            .search(self._get_release_channel_possible_candidate_domain())
            .sorted(key=lambda r: (not bool(r.partner_ids), r.sequence))
        )

    def _get_release_channel_possible_candidate_domain(self):
        self.ensure_one()
        return [
            ("is_manual_assignment", "=", False),
            ("state", "!=", "asleep"),
            "|",
            ("picking_type_ids", "=", False),
            ("picking_type_ids", "in", self.picking_type_id.ids),
            "|",
            ("warehouse_id", "=", False),
            ("warehouse_id", "=", self.picking_type_id.warehouse_id.id),
            "|",
            ("partner_ids", "=", False),
            ("partner_ids", "in", self.partner_id.ids),
        ]
