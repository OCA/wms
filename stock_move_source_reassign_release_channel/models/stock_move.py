# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.osv.expression import AND


class StockMove(models.Model):
    _inherit = "stock.move"

    def _search_picking_for_assignation_domain(self):
        """
        If there was a release channel filled in in the reassignation
        wizard, we will try to reassign the move to a picking with
        the same release channel first.
        """
        domain = super()._search_picking_for_assignation_domain()
        reassign_release_channel_id = self.env.context.get(
            "reassign_release_channel_id"
        )
        if reassign_release_channel_id:
            domain = AND(
                [
                    domain,
                    [("release_channel_id", "=", reassign_release_channel_id)],
                ]
            )
        return domain

    def _get_new_picking_values(self):
        """
        A release channel has been filled in in the reassignation wizard.
        If a new picking is created, fill in the release channel in new values.
        """
        values = super()._get_new_picking_values()
        reassign_release_channel_id = self.env.context.get(
            "reassign_release_channel_id"
        )
        if reassign_release_channel_id:
            values["release_channel_id"] = reassign_release_channel_id
        return values

    def _source_reassign(
        self,
        destination_picking_type,
        transfer_picking_type,
        destination_picking=False,
        strict=True,
        **kwargs,
    ):
        if "reassign_release_channel_id" in kwargs:
            return super(
                StockMove,
                self.with_context(
                    reassign_release_channel_id=kwargs.get(
                        "reassign_release_channel_id"
                    )
                ),
            )._source_reassign(
                destination_picking_type,
                transfer_picking_type,
                destination_picking=destination_picking,
                strict=strict,
                **kwargs,
            )
        return super()._source_reassign(
            destination_picking_type,
            transfer_picking_type,
            destination_picking=destination_picking,
            strict=strict,
            **kwargs,
        )
