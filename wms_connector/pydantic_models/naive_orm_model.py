# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from extendable_pydantic import ExtendableModelMeta

from odoo.addons.pydantic import utils

from pydantic import BaseModel


class NaiveOrmModel(BaseModel, metaclass=ExtendableModelMeta):
    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter
