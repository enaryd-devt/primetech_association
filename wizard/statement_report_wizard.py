# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class AssociationStatementReportWizard(models.TransientModel):
    _name = "association.statement.report.wizard"
    _description = "Assistant de rapports et relevés"

    report_type = fields.Selection([
        ("member_account", "Relevé de compte membre"),
        ("fund", "Relevé de compte de trésorerie"),
        ("committee", "Bureau exécutif"),
        ("discipline_member", "Discipline et sanctions par membre"),
        ("discipline_global", "Rapport global de discipline et sanctions"),
    ], required=True, default="member_account", string="Document")
    date_from = fields.Date(string="Du", required=True, default=lambda self: fields.Date.context_today(self).replace(day=1))
    date_to = fields.Date(string="Au", required=True, default=fields.Date.context_today)
    member_id = fields.Many2one("association.member", string="Membre")
    member_account_id = fields.Many2one("association.member.account", string="Compte membre", domain="[('member_id', '=', member_id)]")
    fund_id = fields.Many2one("association.fund", string="Compte de trésorerie")
    committee_id = fields.Many2one("association.committee", string="Bureau exécutif")

    def _check_parameters(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise ValidationError(_("La date de début doit précéder la date de fin."))
        required = {
            "member_account": self.member_account_id,
            "fund": self.fund_id,
            "committee": self.committee_id,
            "discipline_member": self.member_id,
        }
        if self.report_type in required and not required[self.report_type]:
            raise ValidationError(_("Sélectionnez l'élément à imprimer."))

    def action_print(self):
        self._check_parameters()
        return self.env.ref("primetech_association.action_report_statement").report_action(self)

    def get_lines(self):
        self.ensure_one()
        if self.report_type == "member_account":
            return self.env["association.member.account.transaction"].search([
                ("account_id", "=", self.member_account_id.id),
                ("transaction_date", ">=", self.date_from), ("transaction_date", "<=", self.date_to),
            ], order="transaction_date,id")
        if self.report_type == "fund":
            return self.env["association.fund.transaction"].search([
                ("fund_id", "=", self.fund_id.id),
                ("transaction_date", ">=", self.date_from), ("transaction_date", "<=", self.date_to),
                ("state", "=", "validated"),
            ], order="transaction_date,id")
        if self.report_type.startswith("discipline"):
            domain = [("incident_date", ">=", self.date_from), ("incident_date", "<=", self.date_to)]
            if self.report_type == "discipline_member":
                domain.append(("member_id", "=", self.member_id.id))
            return self.env["association.penalty"].search(domain, order="incident_date,id")
        return self.committee_id.member_line_ids

    def get_report_lines(self):
        rows = []
        for line in self.get_lines():
            date_or_number = (
                getattr(line, "transaction_date", False)
                or getattr(line, "incident_date", False)
                or getattr(line, "sequence", "")
            )
            member = getattr(line, "member_id", False)
            function = getattr(line, "function_id", False)
            rows.append({
                "date": date_or_number,
                "reference": member.display_name if member else getattr(line, "name", ""),
                "description": (
                    getattr(line, "description", False)
                    or getattr(line, "penalty_description", False)
                    or (function.display_name if function else "")
                ),
                "value": (
                    getattr(line, "amount", False)
                    or getattr(line, "penalty_amount", False)
                    or getattr(line, "state", "")
                ),
            })
        return rows
