# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo.addons.component.core import Component


class SchemaDetailAction(Component):
    """Provide advanced details.
    """

    _inherit = "shopfloor.schema.action"
    _name = "shopfloor.schema.detail.action"
    _usage = "schema_detail"
