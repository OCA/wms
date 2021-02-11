# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class StockLocation(models.Model):
    _inherit = "stock.location"

    storage_buffer_ids = fields.Many2many(
        comodel_name="stock.location.storage.buffer",
        relation="stock_location_storage_buffer_stock_location_buffer_rel",
    )
    is_in_storage_buffer = fields.Boolean(
        compute="_compute_is_in_storage_buffer", store=True,
    )

    @api.depends("storage_buffer_ids", "location_id.is_in_storage_buffer")
    def _compute_is_in_storage_buffer(self):
        for location in self:
            if self.storage_buffer_ids:
                location.is_in_storage_buffer = True
            else:
                location.is_in_storage_buffer = (
                    location.location_id.is_in_storage_buffer
                )

    def _should_compute_location_is_empty(self):
        if super()._should_compute_location_is_empty():
            return True
        return self.is_in_storage_buffer

    # add dependency
    @api.depends("is_in_storage_buffer")
    def _compute_location_is_empty(self):
        super()._compute_location_is_empty()

    def _select_final_valid_putaway_locations(self, limit=None):
        """Return the valid locations using the provided limit

        ``self`` contains locations already ordered and contains
        only valid locations.
        This method can be used as a hook to add or remove valid
        locations based on other properties. Pay attention to
        keep the order.
        """
        if self:  # short-circuit computation when already 0 valid
            self = self._filter_locations_blocked_by_buffer()
        return super()._select_final_valid_putaway_locations(limit=limit)

    def _filter_locations_blocked_by_buffer(self):
        valid_location_ids = set(self.ids)
        for storage_buffer in self.env["stock.location.storage.buffer"].search([]):
            # By looking first if the buffer is blocked, we may compute
            # "location_is_empty" for nothing if no valid location was
            # in the blocked locations.
            # But if we first look if we have valid locations amongst the
            # the potentially blocked locations, we have to compute all the
            # leaf locations to find intersections with valid locations, which
            # is costly too.
            # If we have performance issues, it would be worth checking
            # the costs of the two and pick the faster.
            if storage_buffer.buffers_have_capacity():
                # locations behind the buffer are not blocked
                continue
            # as the buffer is full, all the leaf locations behind the buffer
            # are unreachable, remove them from the valid locations
            blocked_locations = storage_buffer.location_ids.leaf_location_ids
            current_valid_count = len(valid_location_ids)
            valid_location_ids -= set(blocked_locations.ids)
            new_valid_count = len(valid_location_ids)
            _logger.debug(
                "%d locations excluded, blocked by buffer locations %s",
                current_valid_count - new_valid_count,
                storage_buffer.buffer_location_ids.mapped("name"),
            )
        # keep the original order
        return self.browse([id_ for id_ in self.ids if id_ in valid_location_ids])
