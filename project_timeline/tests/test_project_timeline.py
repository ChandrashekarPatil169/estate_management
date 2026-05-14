# Copyright 2018 Onestein
# Copyright 2024 Tecnativa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import exceptions, fields
from odoo.tests.common import TransactionCase


class TestProjectTimeline(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env.ref("project.project_project_1")
        cls.stage = cls.env.ref("project.project_stage_2")

        cls.task = cls.env["project.task"].create({
            "name": "Test Task",
            "project_id": cls.project.id,
        })

    # ---------------------------------------------------------
    # Planned dates auto-fill flow
    # ---------------------------------------------------------

    def test_01_flow_filling(self):
        self.assertFalse(self.task.planned_date_start)

        # Assign user properly (M2M command)
        self.task.write({
            "user_ids": [(4, self.env.user.id)]
        })

        self.assertTrue(self.task.planned_date_start)
        self.assertFalse(self.task.planned_date_end)

        self.task.write({
            "stage_id": self.stage.id,
            "date_end": fields.Datetime.add(
                self.task.planned_date_start, days=1
            ),
        })

        self.assertTrue(self.task.planned_date_end)

    # ---------------------------------------------------------
    # No overwrite if dates already exist
    # ---------------------------------------------------------

    def test_02_no_filling(self):
        task = self.env["project.task"].create({
            "name": "No Fill Task",
            "planned_date_start": "2018-05-01 00:00:00",
            "planned_date_end": "2018-05-07 00:00:00",
            "project_id": self.project.id,
        })

        task.write({
            "user_ids": [(4, self.env.user.id)]
        })

        self.assertEqual(
            task.planned_date_start,
            fields.Datetime.to_datetime("2018-05-01 00:00:00")
        )

        task.stage_id = self.stage

        self.assertEqual(
            task.planned_date_end,
            fields.Datetime.to_datetime("2018-05-07 00:00:00")
        )

    # ---------------------------------------------------------
    # Basic date presence
    # ---------------------------------------------------------

    def test_misc_dates(self):
        self.assertFalse(self.task.planned_date_start)
        self.assertFalse(self.task.date_end)

    # ---------------------------------------------------------
    # Valid date logic
    # ---------------------------------------------------------

    def test_valid_dates(self):
        self.task.planned_date_start = fields.Datetime.now()
        self.task.date_end = fields.Datetime.add(
            self.task.planned_date_start,
            days=1,
        )
        self.assertGreater(
            self.task.date_end,
            self.task.planned_date_start
        )

    # ---------------------------------------------------------
    # Invalid date validation
    # ---------------------------------------------------------

    def test_invalid_dates(self):
        self.task.write({
            "user_ids": [(4, self.env.user.id)]
        })

        with self.assertRaises(exceptions.ValidationError):
            self.task.planned_date_end = fields.Datetime.subtract(
                self.task.planned_date_start,
                days=1,
            )