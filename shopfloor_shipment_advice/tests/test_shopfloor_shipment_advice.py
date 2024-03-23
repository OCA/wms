# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields

from odoo.addons.shopfloor.tests.test_actions_data_base import (
    ActionsDataCaseBase,
    ActionsDataDetailCaseBase,
)


class ActionsDataCaseShipment(ActionsDataCaseBase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.dock = cls.env.ref("shipment_advice.stock_dock_demo")
        cls.shipment = cls.env["shipment.advice"].create(
            {
                "shipment_type": "outgoing",
                "dock_id": cls.dock.id,
                "arrival_date": fields.Datetime.now(),
            }
        )

    def _expected_dock(self, record, **kw):
        data = {
            "id": record.id,
            "name": record.name,
        }
        data.update(**kw)
        return data

    def _expected_shipment_advice(self, record, **kw):
        data = {
            "id": record.id,
            "name": record.name,
            "state": record.state,
        }
        data["is_planned"] = bool(record.planned_move_ids)
        if record.dock_id:
            data["dock"] = self._expected_dock(record.dock_id)
        data.update(kw)
        return data

    def test_data_shipment_advice(self):
        data = self.data.shipment_advice(self.shipment)
        self.assert_schema(self.schema.shipment_advice(), data)
        self.assertDictEqual(data, self._expected_shipment_advice(self.shipment))


class ActionsDataDetailCaseBaseShipment(
    ActionsDataCaseShipment, ActionsDataDetailCaseBase
):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        # Add some moves in the shipment advice
        records = cls.picking
        wiz_model = cls.env["wizard.plan.shipment"].with_context(
            active_model=records._name,
            active_ids=records.ids,
        )
        wiz = wiz_model.create({"shipment_advice_id": cls.shipment.id})
        wiz.action_plan()

    def _expected_shipment_advice_detail(self, record, **kw):
        return dict(
            **self._expected_shipment_advice(record),
            **{"planned_moves": self.data_detail.moves(record.planned_move_ids)}
        )

    def test_data_shipment_advice_detail(self):
        data = self.data_detail.shipment_advice_detail(self.shipment)
        self.assert_schema(self.schema_detail.shipment_advice_detail(), data)
        self.assertDictEqual(data, self._expected_shipment_advice_detail(self.shipment))
