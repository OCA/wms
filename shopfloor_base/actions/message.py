# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import _

from odoo.addons.component.core import Component


class MessageAction(Component):
    """Provide message templates

    The methods should be used in Service Components, in order to share as much
    as possible the messages for similar events.

    Before adding a message, please look if no message already exists,
    and consider making an existing message more generic.
    """

    _name = "shopfloor.message.action"
    _inherit = "shopfloor.process.action"
    _usage = "message"

    def generic_record_not_found(self):
        return {
            "message_type": "error",
            "body": _("Record not found."),
        }

    # TODO: we should probably have `shopfloor.message` records
    # and here we can simply lookup for a message using its identifier
    # Eg:
    #
    # def _get_message(self, key):
    #     domain = [
    #         ("type", "=", "action"),
    #         ("key", "=", key),
    #     ]
    #     return self.env["shopfloor.message"].search(domain)
    #
    # def message(self, key, **kw):
    #     msg = self._get_message(key)
    #     return {
    #         "type": msg.type,
    #         "body": msg.body % kw
    #     }
    #
    # then all depending modules can simply create records they need
    # instea of overriding and polluting the component.
    # Additional goodie: users can edit messages via UI.
