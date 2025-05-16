# Copyright 2020 Camptocamp
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _, exceptions, fields, models
from odoo.osv import expression

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
            .search(self._release_channel_possible_candidate_domain)
            .sorted(key=lambda r: (not bool(r.partner_ids), r.sequence))
        )

    @property
    def _release_channel_possible_candidate_domain(self):
        """Domain for finding channel candidates"""
        self.ensure_one()
        domain_base = self._release_channel_possible_candidate_domain_base
        domain = [
            ("is_manual_assignment", "=", False),
            ("state", "in", ("open", "locked")),
            "|",
            ("picking_type_ids", "=", False),
            ("picking_type_ids", "in", self.picking_type_id.ids),
        ]
        domain_partner = (
            self.partner_id._release_channel_possible_candidate_domain
            if self.partner_id
            else []
        )
        domain_extras = []
        if self._release_channel_possible_candidate_domain_apply_extras:
            domain_extras = self._release_channel_possible_candidate_domain_extras
        domain = expression.AND([domain, domain_base, domain_partner] + domain_extras)
        return domain

    @property
    def _release_channel_possible_candidate_domain_base(self):
        """Base domain for finding channel candidates based on picking.

        This is the base domain we always want to apply.

        This is used by stock_release_channel_partner_by_date where you
        can force a channel for a partner on a specific day. This domain is
        used to check if there is a specific channel defined for the warehouse
        (and carrier with delivery module).
        """
        # when a warehouse is defined on the channel, it must always match
        # otherwise fallback on the picking type
        return [
            ("company_id", "=", self.company_id.id),
            "|",
            "&",
            ("warehouse_id", "=", False),
            "|",
            ("picking_type_ids", "=", False),
            ("picking_type_ids", "in", self.picking_type_id.ids),
            ("warehouse_id", "=", self.picking_type_id.warehouse_id.id),
        ]

    @property
    def _release_channel_possible_candidate_domain_extras(self):
        """Additional domains for finding channel candidates based on picking.

        Allow extension modules to add domain rules. Each module can add a
        domain to the list.

        Those domains won't be used by stock_release_channel_partner_by_date
        where you can force a channel for a partner on a specific day.
        """
        return []

    @property
    def _release_channel_possible_candidate_domain_apply_extras(self):
        """Extra domains can be discarded.

        For example, when there is an SO commitment date.
        """
        return True
