# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, fields, models


class StockStorageLocationSequence(models.Model):

    _name = "stock.storage.location.sequence"
    _description = "Sequence of locations to put-away the package storage type"
    _order = "sequence"

    package_storage_type_id = fields.Many2one(
        "stock.package.storage.type", required=True
    )
    sequence = fields.Integer(required=True)
    location_id = fields.Many2one("stock.location", required=True,)
    location_putaway_strategy = fields.Selection(
        related="location_id.pack_putaway_strategy"
    )

    def _format_package_storage_type_message(self, last=False):
        self.ensure_one()
        # TODO improve ugly code
        type_matching_locations = self.location_id.get_storage_locations().filtered(
            lambda l: self.package_storage_type_id
            in l.allowed_location_storage_type_ids.mapped("package_storage_type_ids")
        )
        if type_matching_locations:
            # Get the selection description
            pack_storage_strat = None
            pack_storage_strat_selection = self.location_id._fields[
                "pack_putaway_strategy"
            ]._description_selection(self.env)
            for strat in pack_storage_strat_selection:
                if strat[0] == self.location_id.pack_putaway_strategy:
                    pack_storage_strat = strat[1]
                    break
            msg = ' * <span style="color: green;">{} ({})</span>'.format(
                self.location_id.name, pack_storage_strat,
            )
            if last:
                # If last, we want to check if restrictions are defined on
                # location storage types accepting this package storage type
                # TODO improve ugly code
                loc_st = type_matching_locations.mapped(
                    "allowed_location_storage_type_ids"
                ).filtered(
                    lambda lst: self.package_storage_type_id
                    in lst.package_storage_type_ids
                    and not lst.has_restrictions
                )
                if not loc_st:
                    msg = (
                        _(
                            ' * <span style="color: orange;">%s (WARNING: '
                            "restrictions are active on location storage types "
                            "matching this package storage type)</span>"
                        )
                        % self.location_id.name
                    )
        else:
            msg = (
                _(
                    ' * <span style="color: red;">%s '
                    "(WARNING: no suitable location matching storage type)</span>"
                )
                % self.location_id.name
            )
        return msg

    def button_show_locations(self):
        action = self.env.ref("stock.action_location_form").read()[0]
        action["domain"] = [
            ("parent_path", "=ilike", "{}%".format(self.location_id.parent_path)),
            (
                "allowed_location_storage_type_ids",
                "in",
                self.package_storage_type_id.location_storage_type_ids.ids,
            ),
        ]
        return action
