# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import werkzeug

from odoo import api, models
from odoo.http import request

from odoo.addons.base.models.ir_http import RequestUID


class TechNameConverter(werkzeug.routing.BaseConverter):
    """Record converter via tech_name field.

    Similar to the standard model converter but uses the `tech_name` field
    of a model to retrieve the record.
    """

    def __init__(self, url_map, model=False):
        super().__init__(url_map)
        self.model = model

    def to_python(self, value):
        # First lookup for the query
        query = (
            request.env[self.model].sudo()._search([("tech_name", "=", value)], limit=1)
        )
        # Then browse the record w/ proper environment (as per ModelConverter)
        _uid = RequestUID(value=value, converter=self)
        env = api.Environment(request.cr, _uid, request.context)
        return env[self.model].browse(query)

    def to_url(self, value):
        return value.tech_name


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _get_converters(cls):
        converters = super()._get_converters()
        converters["tech_name"] = TechNameConverter
        return converters
