# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import csv
import datetime
from io import StringIO

from odoo import fields, models
from odoo.tools import config


class SynchronizeExportableMixin(models.AbstractModel):
    _name = "synchronize.exportable.mixin"
    _description = "Synchronizable export mixin"

    wms_export_date = fields.Datetime(readonly=True)
    wms_export_attachment = fields.Many2one(
        "attachment.queue", index=True, readonly=True
    )
    wms_export_error = fields.Char(readonly=True, index=True)

    @property
    def record_per_file(self):
        return 1

    def button_trigger_export(self):
        self.synchronize_export()

    def _get_export_data(self):
        data = []
        records = self.browse()
        sequence = 0
        for rec in self:
            try:
                with self._cr.savepoint():
                    data += rec._prepare_export_data(sequence)
                    records |= rec
                    rec.wms_export_error = None
                    sequence += 1
            except Exception as e:
                if "pdb" in config.get("dev_mode"):
                    raise
                rec.wms_export_error = str(e)
                continue
            if len(records) >= self.record_per_file:
                yield records, data
                data = []
                records = self.browse()
                sequence = 0
        if len(records):
            yield records, data

    def synchronize_export(self):
        for records, data in self._get_export_data():
            vals = self._format_to_exportfile(data)
            attachment = self.env["attachment.queue"].create(vals)
            records.track_export(attachment)

    def track_export(self, attachment):
        self.wms_export_date = datetime.datetime.now()
        self.wms_export_attachment = attachment

    def _prepare_export_data(self, idx) -> list:
        raise NotImplementedError

    # TODO cleanup this code
    def _format_to_exportfile(self, name, data):
        return self._format_to_exportfile_csv(name, data)

    def _format_to_exportfile_csv(self, data):
        csv_file = StringIO()
        delimiter = self.env.context.get("csv_delimiter") or ";"
        writer = csv.DictWriter(
            csv_file, fieldnames=data[0].keys(), delimiter=delimiter
        )
        for row in data:
            writer.writerow(row)
        csv_file.seek(0)
        ast = self.env.context.get("attachment_task")
        return {
            "name": self._get_export_name(),
            "datas": base64.b64encode(csv_file.getvalue().encode("utf-8")),
            "task_id": ast.id,
            "file_type": ast.file_type,
        }

    def _get_export_name(self):
        raise NotImplementedError

    def _schedule_export(self, warehouse, domain=False):
        if not domain:
            domain = []
        recs = self.search(domain)
        if not recs:
            return
        recs.with_context(warehouse=warehouse).synchronize_export()
