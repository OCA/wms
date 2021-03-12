# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import _, api, fields, models


class StockLocationStorageBuffer(models.Model):
    _name = "stock.location.storage.buffer"
    _description = "Location Storage Buffer"

    MAX_LOCATIONS_IN_NAME_GET = 3
    MAX_LOCATIONS_IN_HELP = 10

    buffer_location_ids = fields.Many2many(
        comodel_name="stock.location",
        relation="stock_location_storage_buffer_stock_location_buffer_rel",
        required=True,
        help="Buffers where goods are temporarily stored. When all these "
        "locations contain goods or will receive goods,"
        " the destination locations are not available for putaway.",
    )
    location_ids = fields.Many2many(
        comodel_name="stock.location",
        relation="stock_location_storage_buffer_stock_location_rel",
        required=True,
        help="Destination locations (including sublocations) that will be"
        " unreachable for putaway if the buffers are full.",
    )
    help_message = fields.Html(compute="_compute_help_message")
    active = fields.Boolean(default=True)

    @api.depends("buffer_location_ids", "location_ids")
    def _compute_help_message(self):
        """Generate a description of the storage buffer for humans"""
        for record in self:
            if not (record.buffer_location_ids and record.location_ids):
                record.help_message = _(
                    "<p>Select buffer locations and locations "
                    "blocked for putaways when the buffer locations "
                    "already contain goods or have move lines "
                    "reaching them.</p>"
                )
                continue

            record.help_message = record._help_message()

    def buffers_have_capacity(self):
        self.ensure_one()
        buffer_locations = self.buffer_location_ids.leaf_location_ids
        return any(location.location_is_empty for location in buffer_locations)

    def _help_message_location_items(self, records):
        items = records[: self.MAX_LOCATIONS_IN_HELP].mapped("display_name")
        return items, max(0, len(records) - self.MAX_LOCATIONS_IN_HELP)

    def _prepare_values_for_help_message(self):
        buffer_location_items, buffer_remaining = self._help_message_location_items(
            self.buffer_location_ids.leaf_location_ids
        )
        location_items, loc_remaining = self._help_message_location_items(
            self.location_ids.leaf_location_ids
        )
        return {
            "buffers_have_capacity": self.buffers_have_capacity(),
            "buffer_locations": buffer_location_items,
            "buffer_locations_remaining": buffer_remaining,
            "locations": location_items,
            "locations_remaining": loc_remaining,
        }

    def _help_message(self):
        return self.env["ir.qweb"].render(
            "stock_storage_type_buffer.storage_buffer_help_message",
            self._prepare_values_for_help_message(),
        )

    def name_get(self):
        result = []
        for record in self:
            name = ", ".join(
                record.buffer_location_ids[: self.MAX_LOCATIONS_IN_NAME_GET].mapped(
                    "name"
                )
            )
            if len(record.buffer_location_ids) > self.MAX_LOCATIONS_IN_NAME_GET:
                name += ", ..."
            result.append((record.id, name))
        return result
