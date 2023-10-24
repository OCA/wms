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
    wms_export_date = fields.Date()
    wms_export_attachment = fields.Many2one("attachment.queue", index=True)
    wms_export_error = fields.Char()

    @property
    def file_creation_mode(self):
        return "per_record"

    def button_trigger_export(self):
        self.synchronize_export()

    def _get_export_data(self):
        data = []
        for rec in self.sorted("id"):
            try:
                data += rec._prepare_export_data()
            except Exception as e:
                if "pdb" in config.get("dev_mode"):
                    raise
                rec.wms_export_error = str(e)
                continue
            if self.file_creation_mode == "per_record":
                yield data
                data = []
        if self.file_creation_mode == "per_recordset":
            yield data

    def synchronize_export(self):
        data = self._get_export_data()
        res = self.env["attachment.queue"]
        if self.file_creation_mode == "per_record":
            for el, rec in zip(data, self.sorted("id")):
                attachment = rec._format_to_exportfile(el)
                rec.track_export(attachment)
                res += attachment
        if self.file_creation_mode == "per_recordset":
            res = self._format_to_exportfile(data)
            self.track_export(res)

    def track_export(self, attachment):
        self.wms_export_date = datetime.datetime.now()
        self.wms_export_attachment = attachment

    def _prepare_export_data(self) -> list:
        raise NotImplementedError

    def _format_to_exportfile(self, data):
        return self._format_to_exportfile_csv(data)

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
        vals = {
            "name": self._get_export_name(),
            "datas": base64.b64encode(csv_file.getvalue().encode("utf-8")),
            "task_id": ast.id,
            "file_type": ast.file_type,
        }
        return self.env["attachment.queue"].create(vals)

    def _get_export_name(self):
        raise NotImplementedError

    def _schedule_export(self, warehouse, domain=False):
        if not domain:
            domain = []
        recs = self.search(domain)
        if not recs:
            return
        recs.with_context(warehouse=warehouse).synchronize_export()
