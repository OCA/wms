# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class ShopfloorPickingForm(Component):
    """Allow to modify a stock.picking.

    Editable fields: carrier_id.
    """

    _inherit = "shopfloor.form.mixin"
    _name = "shopfloor.form.stock.picking"
    _usage = "form_edit_stock_picking"
    _description = __doc__
    _expose_model = "stock.picking"

    def _record_data(self, record):
        # TODO: we use _detail here because it has the carrier info
        # but is plenty of data we don't need -> add specific schema for forms
        return self.data_detail.picking_detail(record)

    def _form_data(self, record):
        data = {}
        available_carriers = self._get_available_carriers(record)
        data["carrier_id"] = {
            "value": record.carrier_id.id,
            "select_options": available_carriers.jsonify(["id", "name"]),
        }
        return data

    def _get_available_carriers(self, record):
        company_carriers = self.env["delivery.carrier"].search(
            ["|", ("company_id", "=", False), ("company_id", "=", record.company_id.id)]
        )
        available_carriers = company_carriers.available_carriers(record.partner_id)
        return available_carriers


class ShopfloorPickingFormValidator(Component):
    """Validators for the ShopfloorPickingForm endpoints"""

    _inherit = "shopfloor.form.validator.mixin"
    _name = "shopfloor.form.stock.picking.validator"
    _usage = "form_edit_stock_picking.validator"

    def get(self):
        return {}

    def update(self):
        return {
            "carrier_id": {"type": "integer", "required": True},
        }


class ShopfloorPickingFormValidatorResponse(Component):
    """Validators for the ShopfloorPickingForm endpoints responses"""

    _inherit = "shopfloor.form.validator.response.mixin"
    _name = "shopfloor.form.stock.picking.validator.response"
    _usage = "form_edit_stock_picking.validator.response"

    def _form_schema(self):
        return {
            "carrier_id": self.schemas._schema_dict_of(
                {
                    "value": {"type": "integer", "required": True},
                    "select_options": self.schemas._schema_list_of(
                        self.schemas._simple_record()
                    ),
                }
            )
        }

    def _record_schema(self):
        return self.schemas_detail.picking_detail()
