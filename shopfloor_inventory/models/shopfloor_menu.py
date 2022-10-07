# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, exceptions, fields, models


class ShopfloorMenu(models.Model):
    _inherit = "shopfloor.menu"

    use_existing_inventory = fields.Boolean(
        string="Use only existing inventories",
        default=False,
    )
    use_existing_inventory_is_possible = fields.Boolean(
        compute="_compute_use_existing_inventory_is_possible"
    )
    inventory_zero_counted_quantity = fields.Boolean(
        string="Counted quantities",
        default=True,
    )
    inventory_zero_counted_quantity_is_possible = fields.Boolean(
        compute="_compute_inventory_zero_counted_quantity_is_possible"
    )
    force_inventory_add_product = fields.Boolean(
        string="Add product option",
        default=False,
    )
    force_inventory_add_product_is_possible = fields.Boolean(
        compute="_compute_force_inventory_add_product_is_possible"
    )
    display_location_content = fields.Boolean(
        string="Display location content",
        default=True,
    )
    display_location_content_is_possible = fields.Boolean(
        compute="_compute_display_location_content_is_possible"
    )

    @api.depends("scenario_id")
    def _compute_use_existing_inventory_is_possible(self):
        for menu in self:
            menu.use_existing_inventory_is_possible = menu.scenario_id.has_option(
                "use_existing_inventory"
            )

    @api.depends("scenario_id")
    def _compute_inventory_zero_counted_quantity_is_possible(self):
        for menu in self:
            menu.inventory_zero_counted_quantity_is_possible = (
                menu.scenario_id.has_option("inventory_zero_counted_quantity")
            )

    @api.depends("scenario_id")
    def _compute_force_inventory_add_product_is_possible(self):
        for menu in self:
            menu.force_inventory_add_product_is_possible = menu.scenario_id.has_option(
                "force_inventory_add_product"
            )

    @api.depends("scenario_id")
    def _compute_display_location_content_is_possible(self):
        for menu in self:
            menu.display_location_content_is_possible = menu.scenario_id.has_option(
                "display_location_content"
            )

    @api.constrains(
        "scenario_id", "display_location_content", "inventory_zero_counted_quantity"
    )
    def _check_display_location_content(self):
        for menu in self:
            if (
                not menu.display_location_content
                and not menu.inventory_zero_counted_quantity
            ):
                raise exceptions.ValidationError(
                    _(
                        "Hidding location content is not allowed if inventory quantities are "
                        "not reset to zero for menu {}."
                    ).format(menu.name)
                )
