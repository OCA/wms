# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .naive_orm_model import NaiveOrmModel
from pydantic import validator


class StockPickingExporter(NaiveOrmModel):
    id: int
    name: str

    @validator("name")
    def process_name(self, v):
        # operations on vals
        return v
