# Copyright 2020 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _
from odoo.osv import expression

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component
from odoo.addons.shopfloor_base.exceptions import ShopfloorError


class Inventory(Component):
    """
    Methods for Inventory Process
    """

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.inventory"
    _usage = "inventory"
    _description = __doc__

    def _response_for_start(self, message=None, popup=None):
        return self._response(next_state="start", message=message, popup=popup)

    def _response_for_confirm_start(self, inventory):
        return self._response(
            next_state="confirm_start",
            data=self.data.inventory(inventory),
        )

    def _response_for_manual_selection(self, inventories, message=None):
        data = {
            "records": self.data.inventories(inventories),
            "size": len(inventories),
        }
        return self._response(next_state="manual_selection", data=data, message=message)

    def _response_for_start_location(self, inventory, message=None, popup=None):
        return self._response(
            next_state="start_location",
            data=self._data_inventory_location(inventory),
            message=message,
            popup=popup,
        )

    def _response_for_scan_product(self, inventory, location, message=None):
        data = self._data_inventory_location(inventory, location)
        return self._response(next_state="scan_product", data=data, message=message)

    def _response_for_empty_location(
        self, inventory, location, message=None, popup=None
    ):
        return self._response(
            next_state="empty_location",
            data=self._data_inventory_location(inventory, location),
            message=message,
            popup=popup,
        )

    def _response_inventory_does_not_exist(self):
        return self._response_for_start(message=self.msg_store.record_not_found())

    def find_inventory(self):
        inventories = self._inventory_search()
        selected = self._select_an_inventory(inventories)
        if selected:
            return self._response_for_confirm_start(selected)
        else:
            return self._response_for_start(
                message={
                    "message_type": "info",
                    "body": _("No more work to do, please create a new inventory"),
                },
            )

    def list_inventory(self):
        inventories = self._inventory_search()
        return self._response_for_manual_selection(inventories)

    def select_inventory(self, inventory_id):
        inventories = self._inventory_search(inventory_ids=[inventory_id])
        selected = self._select_an_inventory(inventories)
        if selected:
            return self._response_for_confirm_start(selected)
        else:
            return self._response(
                base_response=self.list_inventory(),
                message={
                    "message_type": "warning",
                    "body": _("This inventory cannot be selected."),
                },
            )

    def _inventory_base_search_domain(self):
        return [
            "|",
            ("user_id", "=", False),
            ("user_id", "=", self.env.user.id),
            ("state", "=", "confirm"),
        ]

    def _inventory_search(self, name_fragment=None, inventory_ids=None):
        domain = self._inventory_base_search_domain()
        if name_fragment:
            domain = expression.AND([domain, [("name", "ilike", name_fragment)]])
        if inventory_ids:
            domain = expression.AND([domain, [("id", "in", inventory_ids)]])
        records = self.env["stock.inventory"].search(domain, order="id asc")
        #        records = records.filtered(self._inventory_filter)
        return records

    def _select_an_inventory(self, inventories):
        # first look for started inventory assigned to self
        candidates = inventories.filtered(
            lambda inv: inv.user_id == self.env.user
            and any(loc.state != "pending" for loc in inv.sub_location_ids)
        )
        if candidates:
            return candidates[0]
        # then look for confirm assigned to self
        candidates = inventories.filtered(lambda inv: inv.user_id == self.env.user)
        if candidates:
            return candidates[0]
        # finally take any inventory that search could return
        if inventories:
            inventory = inventories[0]
            inventory.write({"user_id": self.env.uid})
            return inventory
        return self.env["stock.inventory"]

    def confirm_start(self, inventory_id):
        """User confirms they start an inventory"""
        inventory = self.env["stock.inventory"].browse(inventory_id)
        if not inventory.exists():
            return self._response_inventory_does_not_exist()
        inventory.user_id = self.env.user.id
        if len(inventory.location_ids) == 1 and not inventory.location_ids.child_ids:
            return self._response_for_scan_product(inventory, inventory.location_ids)
        return self._response_for_start_location(inventory)

    def start_location(self, inventory_id, barcode):
        inventory = self.env["stock.inventory"].browse(inventory_id)
        if not inventory.exists():
            return self._response_inventory_does_not_exist()
        search = self._actions_for("search")
        location = search.location_from_scan(barcode)
        if not location:
            return self._response_for_start_location(
                inventory, message=self.msg_store.no_location_found()
            )
        location_state = inventory.sub_location_ids.filtered(
            lambda l: l.location_id == location
        )
        if location_state == "done":
            # TODO re-inventory or update location instead of raise
            raise ShopfloorError(
                self.msg_store.location_already_inventoried(barcode),
                next_state="start_location",
            )
        if location.has_ongoing_operation():
            raise ShopfloorError(
                self.msg_store.has_on_going_operation(location),
                next_state="start_location",
            )
        location_state.action_start()
        return self._response_for_scan_product(inventory, location)

    def scan_product(self, inventory_id, location_id, barcode, quantity=0):
        inventory = self.env["stock.inventory"].browse(inventory_id)
        if not inventory.exists():
            return self._response_inventory_does_not_exist()
        location = self.env["stock.location"].browse(location_id)
        search = self._actions_for("search")
        product = search.product_from_scan(barcode, use_packaging=False)
        if product:
            if product.tracking in ["lot", "serial"]:
                return self._response_for_scan_product(
                    inventory,
                    location,
                    message=self.msg_store.scan_lot_on_product_tracked_by_lot(),
                )
            if quantity:
                self._set_quantity(inventory, location, product, quantity)
            else:
                self._increase_quantity(inventory, location, product)
            return self._response_for_scan_product()
        packaging = search.packaging_from_scan(barcode)
        if packaging:
            if packaging.product_id.tracking in ["lot", "serial"]:
                return self._response_for_scan_product(
                    inventory,
                    location,
                    message=self.msg_store.scan_lot_on_product_tracked_by_lot(),
                )
            product = packaging.product_id
            if quantity:
                self._set_quantity(inventory, location, product, quantity)
            else:
                self._increase_quantity(inventory, location, product)
            return self._response_for_scan_product()
        lot = search.lot_from_scan(barcode)
        if lot:
            product = lot.product_id
            if quantity:
                self._set_quantity(inventory, location, product, quantity, lot=lot)
            else:
                self._increase_quantity(inventory, location, product, lot=lot)
            return self._response_for_scan_product()
        other_location = search.location_from_scan(barcode)
        if other_location and other_location != location:
            return self._location_counted(inventory, location, other_location)
        return self._response_for_scan_product(
            inventory, location, message=self.msg.store.no_product_for_barcode(barcode)
        )


class ShopfloorInventoryValidator(Component):
    """Validators for the Inventory endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.inventory.validator"
    _usage = "inventory.validator"

    def find_inventory(self):
        return {}

    def list_inventory(self):
        return {}

    def select_inventory(self):
        return {
            "inventory_id": {"coerce": to_int, "required": True, "type": "integer"},
        }


class ShopfloorInventoryValidatorResponse(Component):
    """Validators for the Inventory endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.inventory.validator.response"
    _usage = "inventory.validator.response"

    _start_state = "start"

    def _states(self):
        """List of possible next states
        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "start": self._schema_inventory,
            "scan_product": self._schema_line_inventory,
        }

    @property
    def _schema_inventory(self):
        return {
            "inventories": self.schemas._schema_list_of(self.schemas.inventory()),
        }

    @property
    def _schema_line_inventory(self):
        return {
            "inventory_lines": self.schemas._schema_list_of(
                self.schemas_detail.inventory_line()
            ),
            "inventory_id": {"type": "integer", "required": True},
            "selected_location": {
                "type": "integer",
                "required": False,
                "nullable": True,
            },
            "product_scanned_list": {
                "type": "list",
                "schema": {"type": "integer", "required": True},
                "required": True,
            },
        }

    def list_inventory(self):
        return self._response_schema(
            next_states={"start"},
        )

    def select_inventory(self):
        return self._response_schema(
            next_states={"scan_product"},
        )
