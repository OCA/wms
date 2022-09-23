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
            data=self.data.inventory(inventory, with_locations=True),
            message=message,
            popup=popup,
        )

    def _response_for_scan_product(
        self, inventory, location, inventory_line=None, need_confirm=False, message=None
    ):
        data = self._data_inventory_location(
            inventory, location, inventory_line=inventory_line
        )
        next_state = "scan_product" if not need_confirm else "confirm_done"
        return self._response(next_state=next_state, data=data, message=message)

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

    def _data_inventory_location(self, inventory, location, inventory_line=None):
        data = self.data.inventory(inventory)
        lines = self.env["stock.inventory.line"]
        if self.work.menu.display_location_content:
            lines = self._find_inventory_line(
                inventory, location, create=False, multi=True
            )
        if inventory_line:
            lines -= inventory_line
        data.update(
            {
                "location": self.data.location(location),
                "lines": self.data.inventory_lines(lines),
                "current_line": self.data.inventory_line(inventory_line),
                "display_location_content": self.work.menu.display_location_content,
            }
        )
        return data

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
            ("shopfloor_validated", "!=", True),
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
            inventory.sudo().write({"user_id": self.env.uid})
            return inventory
        return self.env["stock.inventory"]

    def confirm_start(self, inventory_id):
        """User confirms they start an inventory"""
        inventory = self.env["stock.inventory"].browse(inventory_id)
        if not inventory.exists():
            return self._response_inventory_does_not_exist()
        inventory.user_id = self.env.user.id
        if len(inventory.location_ids) == 1 and not inventory.location_ids.child_ids:
            self._start_location_state(inventory, inventory.location_ids)
            return self._response_for_scan_product(inventory, inventory.location_ids)
        return self._response_for_start_location(inventory)

    def _start_location_state(self, inventory, location):
        location_state = inventory.sub_location_ids.filtered(
            lambda l: l.location_id == location
        )
        if location_state.state == "done":
            # TODO re-inventory or update location instead of raise
            raise ShopfloorError(
                self.msg_store.location_already_inventoried(location.barcode),
                data=self.data.inventory(inventory, with_locations=True),
                next_state="start_location",
            )
        if location.has_on_going_operation():
            raise ShopfloorError(
                self.msg_store.location_has_on_going_operation(location),
                next_state="start_location",
                data=self.data.inventory(inventory, with_locations=True),
            )
        location_state.action_start()

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
        self._start_location_state(inventory, location)
        return self._response_for_scan_product(inventory, location)

    def scan_product(
        self, inventory_id, location_id, barcode, line_id=None, quantity=0
    ):
        inventory = self.env["stock.inventory"].browse(inventory_id)
        if not inventory.exists():
            return self._response_inventory_does_not_exist()
        location = self.env["stock.location"].browse(location_id)
        current_line = self.env["stock.inventory.line"].browse(line_id)
        search = self._actions_for("search")
        product = search.product_from_scan(barcode, use_packaging=False)
        lot = self.env["stock.production.lot"]
        if not product:
            packaging = search.packaging_from_scan(barcode)
            product = packaging.product_id
        if product and product.tracking in ["lot", "serial"]:
            return self._response_for_scan_product(
                inventory,
                location,
                message=self.msg_store.scan_lot_on_product_tracked_by_lot(),
            )
        if not product:
            lot = search.lot_from_scan(barcode)
        if not product and not lot:
            other_location = search.location_from_scan(barcode)
            if other_location and other_location != location:
                return self._location_inventoried(inventory, location, other_location)
            return self._response_for_scan_product(
                inventory,
                location,
                message=self.msg_store.no_product_for_barcode(barcode),
            )
        line = self._find_inventory_line(inventory, location, product=product, lot=lot)
        if line:
            product = lot.product_id
            if quantity and current_line:
                # we scan another product without validate the qty
                if current_line and current_line != line:
                    self._set_quantity(current_line, quantity)
                    self._increase_quantity(line)
                else:
                    # we scan several time the same product
                    if quantity == current_line.product_qty:
                        self._increase_quantity(current_line)
                    else:
                        self._set_quantity(line, quantity)
            else:
                self._increase_quantity(line)
            return self._response_for_scan_product(
                inventory, location, inventory_line=line
            )
        return self._response_for_scan_product(
            inventory, location, message=self.msg_store.no_product_for_barcode(barcode)
        )

    def confirm_line_qty(self, inventory_id, location_id, line_id, quantity=0):
        inventory = self.env["stock.inventory"].browse(inventory_id)
        if not inventory.exists():
            return self._response_inventory_does_not_exist()
        location = self.env["stock.location"].browse(location_id)
        line = self.env["stock.inventory.line"].browse(line_id)
        self._set_quantity(line, quantity)
        return self._response_for_scan_product(inventory, location)

    def _increase_quantity(self, line):
        if not self.work.menu.inventory_zero_counted_quantity:
            # TODO
            raise ShopfloorError(
                _("increase qty with prefill counted quantity not implemented")
            )
        line.product_qty += 1

    def _set_quantity(self, line, quantity):
        line.product_qty = quantity

    def _find_inventory_line(
        self, inventory, location, product=None, lot=None, create=True, multi=False
    ):
        if inventory.state == "done":
            raise ShopfloorError(
                self.msg_store.inventory_already_done(inventory),
                next_state="start",
            )
        domain = [
            ("inventory_id", "=", inventory.id),
            ("location_id", "=", location.id),
        ]
        if product:
            domain += [("product_id", "=", product.id)]
        if lot:
            domain += [("prod_lot_id", "in", lot.ids)]
        line = self.env["stock.inventory.line"].search(
            domain, order="product_qty", limit=15
        )
        if not line and create:
            if self.work.menu.force_inventory_add_product:
                raise ShopfloorError(
                    _("No inventory line found, please use button 'Add product'")
                )
            line = self._create_inventory_line(
                inventory, location, product=product, lot=lot
            )
        if len(line) > 1 and not multi:
            # TODO
            raise ShopfloorError(
                "Several lines found for location product lot",
                next_state="scan_product",
            )
        return line

    def _create_inventory_line(self, inventory, location, product=None, lot=None):
        if not lot and not product:
            raise ShopfloorError(
                self.msg_store.product_or_lot_mandatory(),
                next_state="scan_product",
                data=self._data_inventory_location(inventory, location),
            )
        if lot and not product:
            if len(lot) > 1:
                # TODO
                raise ShopfloorError(_("Several lot found"))
            product = lot.product_id
        line = self.env["stock.inventory.line"].create(
            {
                "inventory_id": inventory.id,
                "location_id": location.id,
                "product_id": product.id,
                "prod_lot_id": lot.id,
            },
        )
        line.action_refresh_quantity()
        return line

    def _location_inventoried(
        self, inventory, location, other_location=None, confirmation=False
    ):
        lines = self._find_inventory_line(inventory, location, create=False, multi=True)
        if lines.filtered(lambda l: l.product_qty == 0) and not confirmation:
            return self._response_for_scan_product(
                inventory,
                location,
                need_confirm=True,
                message=self.msg_store.location_not_done(),
            )
        location_state = inventory.sub_location_ids.filtered(
            lambda l: l.location_id == location
        )
        location_state.action_done()
        if other_location:
            return self._response_for_scan_product(
                inventory,
                other_location,
                message=self.msg_store.location_inventoried(location),
            )
        return self._response_for_start_location(
            inventory,
            message=self.msg_store.location_inventoried(location),
        )

    def location_inventoried(self, inventory_id, location_id, confirmation=False):
        inventory = self.env["stock.inventory"].browse(inventory_id)
        if not inventory.exists():
            return self._response_inventory_does_not_exist()
        location = self.env["stock.location"].browse(location_id)
        return self._location_inventoried(
            inventory, location, confirmation=confirmation
        )

    def empty_location(self, inventory_id, location_id):
        inventory = self.env["stock.inventory"].browse(inventory_id)
        if not inventory.exists():
            return self._response_inventory_does_not_exist()
        location = self.env["stock.location"].browse(location_id)
        lines = self._find_inventory_line(inventory, location, create=False, multi=True)
        lines.write({"product_qty": 0})
        return self._response_for_start_location(inventory)

    def done_inventory(self, inventory_id):
        inventory = self.env["stock.inventory"].browse(inventory_id)
        if not inventory.exists():
            return self._response_inventory_does_not_exist()
        location_state = inventory.sub_location_ids.filtered(
            lambda l: l.state != "done"
        )
        if location_state:
            return self._response_for_start_location(
                inventory,
                message=self.msg_store.inventory_location_not_done(),
            )
        # TODO sudo because only manager stock can validate inventory
        #        inventory.with_context(_sf_inventory=True).sudo().action_validate()
        inventory.shopfloor_validated = True
        return self._response_for_start(
            message=self.msg_store.inventory_done(inventory)
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

    def confirm_start(self):
        return {
            "inventory_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def start_location(self):
        return {
            "inventory_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def scan_product(self):
        return {
            "inventory_id": {"coerce": to_int, "required": True, "type": "integer"},
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
            "line_id": {
                "coerce": to_int,
                "required": False,
                "type": "integer",
                "nullable": True,
            },
            "quantity": {"coerce": to_int, "required": False, "type": "float"},
        }

    def confirm_line_qty(self):
        return {
            "inventory_id": {"coerce": to_int, "required": True, "type": "integer"},
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "quantity": {"coerce": to_int, "required": False, "type": "float"},
        }

    def location_inventoried(self):
        return {
            "inventory_id": {"coerce": to_int, "required": True, "type": "integer"},
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }

    def empty_location(self):
        return {
            "inventory_id": {"coerce": to_int, "required": True, "type": "integer"},
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def done_inventory(self):
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
            "start": {},
            "confirm_start": self._schema_inventory,
            "start_location": self._schema_inventory_detail,
            "scan_product": self._schema_line_inventory,
            "confirm_done": self._schema_inventory_detail,
            "manual_selection": self._schema_inventory_selection,
        }

    @property
    def _schema_inventories(self):
        return {
            "inventories": self.schemas._schema_list_of(self.schemas.inventory()),
        }

    @property
    def _schema_inventory(self):
        return self.schemas.inventory()

    @property
    def _schema_inventory_detail(self):
        return self.schemas.inventory(with_locations=True)

    @property
    def _schema_line_inventory(self):
        schema = self.schemas.inventory()
        schema.update(
            {
                "location": self.schemas._schema_dict_of(self.schemas.location()),
                "lines": self.schemas._schema_list_of(self.schemas.inventory_line()),
                "current_line": self.schemas._schema_dict_of(
                    self.schemas.inventory_line()
                ),
                "display_location_content": {
                    "type": "boolean",
                    "nullable": False,
                    "required": True,
                },
            }
        )
        return schema

    @property
    def _schema_inventory_selection(self):
        return self.schemas._schema_search_results_of(self.schemas.inventory())

    def find_inventory(self):
        return self._response_schema(next_states={"confirm_start"})

    def list_inventory(self):
        return self._response_schema(
            next_states={"manual_selection"},
        )

    def select_inventory(self):
        return self._response_schema(
            next_states={"confirm_start"},
        )

    def confirm_start(self):
        return self._response_schema(
            next_states={
                "start_location",
                # when there is only one location to inventory
                "scan_product",
            }
        )

    def start_location(self):
        return self._response_schema(
            next_states={
                "scan_product",
                "start_location",
            }
        )

    def scan_product(self):
        return self._response_schema(
            next_states={
                "scan_product",
            }
        )

    def empty_location(self):
        return self._response_schema(
            next_states={
                "start_location",
            }
        )

    def done_inventory(self):
        return self._response_schema(
            next_states={
                "start",
                # when inventory not done
                "start_location",
            }
        )
