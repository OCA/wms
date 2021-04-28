# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2020 Akretion (http://www.akretion.com)
# Copyright 2020-2021 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from werkzeug.exceptions import BadRequest

from odoo import _, exceptions
from odoo.exceptions import MissingError
from odoo.http import request
from odoo.osv import expression

from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.component.core import AbstractComponent, WorkContext


def to_float(val):
    if isinstance(val, float):
        return val
    if val:
        return float(val)
    return None


class BaseShopfloorService(AbstractComponent):
    """Base class for REST services"""

    _inherit = "base.rest.service"
    _name = "base.shopfloor.service"
    _collection = "shopfloor.service"
    _actions_collection_name = "shopfloor.action"
    _expose_model = None
    _log_calls_in_db = True

    def dispatch(self, method_name, *args, params=None):
        self._validate_headers_update_work_context(request, method_name)
        return super().dispatch(method_name, *args, params=params)

    def _get(self, _id):
        domain = expression.normalize_domain(self._get_base_search_domain())
        domain = expression.AND([domain, [("id", "=", _id)]])
        record = self.env[self._expose_model].search(domain)
        if not record:
            raise MissingError(
                _("The record %s %s does not exist") % (self._expose_model, _id)
            )
        else:
            return record

    def _get_base_search_domain(self):
        return []

    def _convert_one_record(self, record):
        """To implement in service Components"""
        return {}

    def _to_json(self, records):
        res = []
        for record in records:
            res.append(self._convert_one_record(record))
        return res

    def _response(
        self, base_response=None, data=None, next_state=None, message=None, popup=None
    ):
        """Base "envelope" for the responses

        All the keys are optional.

        :param base_response: optional dictionary of values to extend
        (typically already created by a call to _response())
        :param data: dictionary of values, when a next_state is provided,
        the data is enclosed in a key of the same name (to support polymorphism
        in the schema)
        :param next_state: string describing the next state that the client
        application must reach
        :param message: dictionary for the message to show in the client
        application (see ``_response_schema`` for the keys)
        :param popup: dictionary for a popup to show in the client application
        (see ``_response_schema`` for the keys). The popup is displayed before
        reaching the next state.
        """
        if base_response:
            response = base_response.copy()
        else:
            response = {}
        if next_state:
            # data for a state is always enclosed in a key with the name
            # of the state, so an endpoint can return to different states
            # that need different data: the schema can be different for
            # every state this way
            response.update(
                {
                    # ensure we have an empty dict when the state
                    # does not need any data, so the client does not need
                    # to check this
                    "data": {next_state: data or {}},
                    "next_state": next_state,
                }
            )

        elif data:
            response["data"] = data

        if message:
            response["message"] = message

        if popup:
            response["popup"] = popup

        return response

    def _response_schema(self, data_schema=None):
        """Schema for the return validator

        Must be used for the schema of all responses.
        The "data" part can be customized and is optional,
        it must be a dictionary.
        """
        if not data_schema:
            data_schema = {}
        return {
            "data": {"type": "dict", "required": False, "schema": data_schema},
            "state": {"type": "string", "required": False},
            "message": {
                "type": "dict",
                "required": False,
                "schema": {
                    "message_type": {
                        "type": "string",
                        "required": True,
                        "allowed": ["info", "warning", "error"],
                    },
                    "title": {"type": "string", "required": False},
                    "body": {"type": "string", "required": True},
                },
            },
        }

    def _get_openapi_default_parameters(self):
        defaults = super()._get_openapi_default_parameters()
        # Normal users can't read an API key, ignore it using sudo() only
        # because it's a demo key.
        demo_api_key = self.env.ref("shopfloor.api_key_demo", raise_if_not_found=False)
        if demo_api_key:
            demo_api_key = demo_api_key.sudo()

        service_params = [
            {
                "name": "API-KEY",
                "in": "header",
                "description": "API key for Authorization",
                "required": True,
                "schema": {"type": "string"},
                "style": "simple",
                "value": demo_api_key.key if demo_api_key else "",
            },
        ]
        if self._requires_header_menu:
            # Try to first the first menu that implements the current service.
            # Not all usages have a process, in that case, we'll set the first
            # menu found
            menu = self.env["shopfloor.menu"].search(
                [("scenario", "=", self._usage)], limit=1
            )
            if not menu:
                menu = self.env["shopfloor.menu"].search([], limit=1)
            service_params.append(
                {
                    "name": "SERVICE_CTX_MENU_ID",
                    "in": "header",
                    "description": "ID of the current menu",
                    "required": True,
                    "schema": {"type": "integer"},
                    "style": "simple",
                    "value": menu.id,
                }
            )
        if self._requires_header_profile:
            profile = self.env["shopfloor.profile"].search([], limit=1)
            service_params.append(
                {
                    "name": "SERVICE_CTX_PROFILE_ID",
                    "in": "header",
                    "description": "ID of the current profile",
                    "required": True,
                    "schema": {"type": "integer"},
                    "style": "simple",
                    "value": profile.id,
                }
            ),
        defaults.extend(service_params)
        return defaults

    @property
    def actions_collection(self):
        return _PseudoCollection(self._actions_collection_name, self.env)

    def actions_for(self, usage, propagate_kwargs=None, **kw):
        """Return an Action Component for a usage

        Action Components are the components supporting the business logic of
        the processes, so we can limit the code in Services to the minimum and
        share methods.
        """
        propagate_kwargs = self.work._propagate_kwargs[:] + (propagate_kwargs or [])
        # propagate custom arguments (such as menu ID/profile ID)
        kwargs = {
            attr_name: getattr(self.work, attr_name)
            for attr_name in propagate_kwargs
            if attr_name not in ("collection", "components_registry")
            and hasattr(self.work, attr_name)
        }
        kwargs.update(kw)
        work = WorkContext(collection=self.actions_collection, **kwargs)
        return work.component(usage=usage)

    def _is_public_api_method(self, method_name):
        # do not "hide" the "actions_for" method as internal since, we'll use
        # it in components, so exclude it from the rest API
        if method_name == "actions_for":
            return False
        return super()._is_public_api_method(method_name)

    @property
    def data(self):
        return self.actions_for("data")

    @property
    def data_detail(self):
        return self.actions_for("data_detail")

    @property
    def msg_store(self):
        return self.actions_for("message")

    @property
    def search_move_line(self):
        # TODO: propagating `picking_types` should probably be default
        return self._actions_for("search_move_line", propagate_kwargs=["picking_types"])


class BaseShopfloorProcess(AbstractComponent):

    _inherit = "base.shopfloor.process"

    def _get_process_picking_types(self):
        """Return picking types for the menu"""
        return self.work.menu.picking_type_ids

    @property
    def picking_types(self):
        if not hasattr(self.work, "picking_types"):
            self.work.picking_types = self._get_process_picking_types()
        if not self.work.picking_types:
            raise exceptions.UserError(
                _("No operation types configured on menu {}.").format(
                    self.work.menu.name
                )
            )
        return self.work.picking_types

    @property
    def search_move_line(self):
        # TODO: picking types should be set somehow straight in the work context
        # by `_validate_headers_update_work_context` in this way
        # we can remove this override and the need to call `_get_process_picking_types`
        # every time.
        return self._actions_for("search_move_line", picking_types=self.picking_types)

    def _check_picking_status(self, pickings):
        """Check if given pickings can be processed.

        If the picking is already done, canceled or didn't belong to the
        expected picking type, a message is returned.
        """
        for picking in pickings:
            if not picking.exists():
                return self.msg_store.stock_picking_not_found()
            if picking.state == "done":
                return self.msg_store.already_done()
            if picking.state != "assigned":  # the picking must be ready
                return self.msg_store.stock_picking_not_available(picking)
            if picking.picking_type_id not in self.picking_types:
                return self.msg_store.cannot_move_something_in_picking_type()

    def is_src_location_valid(self, location):
        """Check the source location is valid for given process.

        We ensure the source is valid regarding one of the picking types of the
        process.
        """
        return location.is_sublocation_of(self.picking_types.default_location_src_id)

    def is_dest_location_valid(self, moves, location):
        """Check the destination location is valid for given moves.

        We ensure the destination is either valid regarding the picking
        destination location or the move destination location. With the push
        rules in the module stock_dynamic_routing in OCA/wms, it is possible
        that the move destination is not anymore a child of the picking default
        destination (as it is the last pushed move that now respects this
        condition and not anymore this one that has a destination to an
        intermediate location)
        """
        return location.is_sublocation_of(
            moves.picking_id.location_dest_id, func=all
        ) or location.is_sublocation_of(moves.location_dest_id, func=all)

    def is_dest_location_to_confirm(self, location_dest_id, location):
        """Check the destination location requires confirmation

        The location is valid but not the expected one: ask for confirmation
        """
        return not location.is_sublocation_of(location_dest_id)
