# Copyright 2022 Brian McMaster <brian@mcmpest.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo.addons.component.core import Component


class ShopfloorUser(Component):
    _inherit = "shopfloor.user"

    @property
    def _user_info_parser(self):
        res = super()._user_info_parser
        res.append(
            ("shopfloor_default_profile_ids:default_profile", self._user_profile_parser)
        )
        return res

    def _user_profile_parser(self, rec, fname):
        profile = (
            rec[fname]
            .filtered(lambda x: x.shopfloor_app_id == self.collection)
            .profile_id
        )
        if not profile:
            return
        profiles_comp = self.component("profile")
        return profiles_comp._convert_one_record(profile)


class ShopfloorUserValidatorResponse(Component):
    _inherit = "shopfloor.user.validator.response"

    def _user_info_schema(self):
        profile_return_validator = self.component("profile.validator.response")
        res = super()._user_info_schema()
        res["default_profile"] = {
            "type": "dict",
            "nullable": True,
            "required": False,
            "schema": profile_return_validator._record_schema,
        }
        return res
