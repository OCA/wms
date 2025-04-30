# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models


class StockPackageType(models.Model):
    _inherit = "stock.package.type"

    product_packaging_ids = fields.One2many("product.packaging", "package_type_id")
    storage_location_sequence_ids = fields.One2many(
        "stock.storage.location.sequence",
        "package_type_id",
        string="Put-Away sequence",
    )
    storage_type_message = fields.Html(compute="_compute_storage_type_message")
    height_required = fields.Boolean(
        string="Height required for packages",
        help=("Height is mandatory for packages configured with this package type."),
        default=False,
    )
    barcode = fields.Char(copy=False)
    # TODO: Check if this is convenient with the constraint on barcode field
    # in core module
    active = fields.Boolean(default=True)

    @api.depends("storage_location_sequence_ids")
    def _compute_storage_type_message(self):
        for package_type in self:
            storage_locations = package_type.storage_location_sequence_ids
            if storage_locations:
                formatted_storage_locations_msgs = []
                last = False
                for sl in storage_locations:
                    # check if we're on the last element
                    if sl == storage_locations[-1]:
                        last = True
                    formatted_storage_locations_msgs.append(
                        sl._format_package_type_message(last=last)
                    )
                msg = _(
                    "When a package with type {name} is put away, the "
                    "strategy will look for an allowed location in the "
                    "following locations: <br/><br/>"
                    "{message} <br/><br/>"
                    "<b>Note</b>: this happens as long as these locations <u>"
                    "are children of the stock move destination location</u> "
                    "or as long as these locations are children of the "
                    "destination location after the (product or category) "
                    "put-away is applied."
                ).format(
                    name=package_type.name,
                    message="<br/>".join(formatted_storage_locations_msgs),
                )
            else:
                msg = _(
                    '<span style="color: red;">The "Put-Away sequence" '
                    "must be defined in order to put away packages using "
                    "this package type ({storage}).</span>"
                ).format(storage=package_type.name)
            package_type.storage_type_message = msg

    def action_view_storage_locations(self):
        return {
            "name": _("Put-away sequence"),
            "type": "ir.actions.act_window",
            "res_model": "stock.storage.location.sequence",
            "view_mode": "list",
            "domain": [("package_type_id", "=", self.id)],
            "context": {"default_package_type_id": self.id},
        }
