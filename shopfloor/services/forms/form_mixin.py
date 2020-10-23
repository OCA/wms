# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _

from odoo.addons.component.core import AbstractComponent


class ShopfloorFormMixin(AbstractComponent):
    """Allow to edit records.
    """

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.form.mixin"
    _usage = "form_mixin"
    _description = __doc__
    _expose_model = ""
    _requires_header_profile = True
    _requires_header_menu = False

    def get(self, _id):
        record = self._get(_id)
        return self._response_for_form(record)

    def update(self, _id, **params):
        record = self._get(_id)
        record.write(self._prepare_params(params, mode="update"))
        return self._response_for_form(record, message=self._msg_record_updated(record))

    def _response_for_form(self, record, **kw):
        record_data = self._record_data(record)
        form_data = self._form_data(record)
        return self._response(data={"record": record_data, "form": form_data}, **kw)

    def _record_data(self, record):
        raise NotImplementedError()

    def _form_data(self, record):
        raise NotImplementedError()

    def _prepare_params(self, params, mode="update"):
        return params

    def _msg_record_updated(self, record):
        model = self.env["ir.model"]._get(record._name)
        body = _("%s updated.") % model.name
        return {"message_type": "info", "body": body}


class ShopfloorFormMixinValidator(AbstractComponent):
    """Validators for the ShopfloorFormMixin endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.form.validator.mixin"
    _usage = "form_mixin.validator"

    def get(self):
        raise NotImplementedError()

    def update(self):
        raise NotImplementedError()


class ShopfloorFormMixinValidatorResponse(AbstractComponent):
    """Validators for the ShopfloorFormMixin endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.form.validator.response.mixin"
    _usage = "form_mixin.validator.response"

    def get(self):
        schema = {
            "record": self.schemas._schema_dict_of(self._record_schema()),
            "form": self.schemas._schema_dict_of(self._form_schema()),
        }
        return self._response_schema(schema)

    def update(self):
        return self.get()

    def _record_schema(self):
        raise NotImplementedError()

    def _form_schema(self):
        raise NotImplementedError()
