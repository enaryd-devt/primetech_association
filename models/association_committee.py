# -*- coding: utf-8 -*-

##############################################################################
#
#    PrimeTech Association Management
#    Copyright (C) 2026 PrimeTech Services
#
#    Author: PrimeTech Services
#    License LGPL-3
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AssociationCommittee(models.Model):
    _name = "association.committee"
    _description = "Bureau Exécutif"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_date desc, id desc"

    # ==========================================================
    # TECHNIQUE
    # ==========================================================

    active = fields.Boolean(
        string="Actif",
        default=True,
        tracking=True,
    )

    sequence = fields.Integer(
        string="Séquence",
        default=10,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Filiale",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    color = fields.Integer(
        string="Couleur",
    )

    # ==========================================================
    # IDENTIFICATION
    # ==========================================================

    name = fields.Char(
        string="Bureau Exécutif",
        required=True,
        tracking=True,
        translate=True,
        help="Exemple : Bureau Exécutif 2026-2029",
    )

    code = fields.Char(
        string="Référence",
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("Nouveau"),
        tracking=True,
    )

    description = fields.Text(
        string="Description",
        translate=True,
    )

    # ==========================================================
    # COMPOSITION DU BUREAU
    # ==========================================================

    member_line_ids = fields.One2many(
        comodel_name="association.committee.line",
        inverse_name="committee_id",
        string="Composition du Bureau",
        copy=True,
    )

    # ==========================================================
    # MANDAT
    # ==========================================================

    start_date = fields.Date(
        string="Date de début",
        required=True,
        tracking=True,
    )

    end_date = fields.Date(
        string="Date de fin",
        required=True,
        tracking=True,
    )

    state = fields.Selection(
        selection=[
            ("draft", "Brouillon"),
            ("running", "En cours"),
            ("expired", "Expiré"),
            ("cancelled", "Annulé"),
        ],
        string="Statut",
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )

    # ==========================================================
    # STATISTIQUES
    # ==========================================================

    member_count = fields.Integer(
        string="Nombre de membres",
        compute="_compute_committee_statistics",
    )

    signatory_count = fields.Integer(
        string="Nombre de signataires",
        compute="_compute_committee_statistics",
    )

    financial_count = fields.Integer(
        string="Nombre de responsables financiers",
        compute="_compute_committee_statistics",
    )


    # ==========================================================
    # CALCUL DES STATISTIQUES
    # ==========================================================

    @api.depends(
        "member_line_ids.member_id",
        "member_line_ids.is_signatory",
        "member_line_ids.is_financial",
    )
    def _compute_committee_statistics(self):
        for rec in self:
            lines = rec.member_line_ids

            rec.member_count = len(lines)

            rec.signatory_count = len(
                lines.filtered("is_signatory")
            )

            rec.financial_count = len(
                lines.filtered("is_financial")
            )

    # ==========================================================
    # NOTES
    # ==========================================================

    note = fields.Html(
        string="Notes internes",
    )

    # ==========================================================
    # CONTRAINTES
    # ==========================================================

    _sql_constraints = [
        (
            "association_committee_code_unique",
            "unique(code, company_id)",
            "La référence du Bureau Exécutif doit être unique par société.",
        ),
    ]

    # ==========================================================
    # COMPUTE
    # ==========================================================

    @api.depends(
        "member_line_ids",
        "member_line_ids.is_signatory",
        "member_line_ids.is_financial",
    )
    def _compute_member_count(self):
        for rec in self:
            rec.member_count = len(rec.member_line_ids)

            rec.signatory_count = len(
                rec.member_line_ids.filtered(
                    lambda line: line.is_signatory
                )
            )

            rec.financial_count = len(
                rec.member_line_ids.filtered(
                    lambda line: line.is_financial
                )
            )

    # ==========================================================
    # CREATE
    # ==========================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", _("Nouveau")) == _("Nouveau"):
                vals["code"] = (
                    self.env["ir.sequence"].next_by_code(
                        "association.committee"
                    )
                    or _("Nouveau")
                )

        return super().create(vals_list)

    # ==========================================================
    # CONTRAINTES MÉTIER
    # ==========================================================

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for rec in self:
            if (
                rec.start_date
                and rec.end_date
                and rec.end_date < rec.start_date
            ):
                raise ValidationError(
                    _(
                        "La date de fin du mandat ne peut pas "
                        "être antérieure à la date de début."
                    )
                )

    @api.constrains(
        "member_line_ids",
        "member_line_ids.member_id",
    )
    def _check_duplicate_members(self):
        for rec in self:
            member_ids = rec.member_line_ids.mapped("member_id").ids

            if len(member_ids) != len(set(member_ids)):
                raise ValidationError(
                    _(
                        "Un membre ne peut apparaître qu'une seule fois "
                        "dans le même Bureau Exécutif."
                    )
                )

    # ==========================================================
    # ACTIONS WORKFLOW
    # ==========================================================

    def action_start(self):
        for rec in self:
            if not rec.member_line_ids:
                raise ValidationError(
                    _(
                        "Vous devez ajouter au moins un membre "
                        "avant de démarrer le mandat."
                    )
                )

            rec.write({
                "state": "running",
            })

            rec.message_post(
                body=_("Le mandat du Bureau Exécutif a été démarré.")
            )

        return True

    def action_expire(self):
        for rec in self:
            rec.write({
                "state": "expired",
            })

            rec.message_post(
                body=_("Le mandat du Bureau Exécutif a été clôturé.")
            )

        return True

    def action_cancel(self):
        for rec in self:
            rec.write({
                "state": "cancelled",
            })

            rec.message_post(
                body=_("Le Bureau Exécutif a été annulé.")
            )

        return True

    def action_reset_draft(self):
        for rec in self:
            rec.write({
                "state": "draft",
            })

            rec.message_post(
                body=_("Le Bureau Exécutif a été remis en brouillon.")
            )

        return True