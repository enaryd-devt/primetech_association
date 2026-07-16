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

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AssociationCard(models.Model):
    _name = "association.card"
    _description = "Carte de membre"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "issue_date desc, id desc"
    _rec_name = "card_number"

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
        tracking=True,
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Devise",
        related="company_id.currency_id",
        readonly=True,
        store=True,
    )

    color = fields.Integer(
        string="Indice de couleur",
    )

    # ==========================================================
    # IDENTIFICATION DE LA CARTE
    # ==========================================================

    card_number = fields.Char(
        string="Numéro de carte",
        required=True,
        copy=False,
        readonly=True,
        default="Nouveau",
        index=True,
        tracking=True,
    )

    name = fields.Char(
        string="Libellé",
        compute="_compute_name",
        store=True,
    )

    # ==========================================================
    # MEMBRE
    # ==========================================================

    member_id = fields.Many2one(
        comodel_name="association.member",
        string="Membre",
        required=True,
        ondelete="restrict",
        index=True,
        tracking=True,
    )

    member_code = fields.Char(
        related="member_id.member_code",
        string="Code membre",
        readonly=True,
        store=True,
    )

    member_name = fields.Char(
        related="member_id.name",
        string="Nom du membre",
        readonly=True,
        store=True,
    )

    image_128 = fields.Image(
        related="member_id.image_128",
        string="Photo",
        readonly=True,
    )

    category_id = fields.Many2one(
        related="member_id.category_id",
        string="Catégorie",
        readonly=True,
        store=True,
    )

    function_id = fields.Many2one(
        related="member_id.function_id",
        string="Fonction",
        readonly=True,
        store=True,
    )

    phone = fields.Char(
        related="member_id.phone",
        string="Téléphone",
        readonly=True,
    )

    email = fields.Char(
        related="member_id.email",
        string="E-mail",
        readonly=True,
    )

    # ==========================================================
    # VALIDITÉ
    # ==========================================================

    issue_date = fields.Date(
        string="Date d'émission",
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )

    validity_months = fields.Integer(
        string="Durée de validité",
        default=12,
        required=True,
        tracking=True,
        help="Durée de validité de la carte en mois.",
    )

    expiry_date = fields.Date(
        string="Date d'expiration",
        compute="_compute_expiry_date",
        store=True,
        tracking=True,
    )

    remaining_days = fields.Integer(
        string="Jours restants",
        compute="_compute_card_information",
    )

    is_expired = fields.Boolean(
        string="Carte expirée",
        compute="_compute_card_information",
    )

    # ==========================================================
    # ÉTAT
    # ==========================================================

    state = fields.Selection(
        selection=[
            ("draft", "Brouillon"),
            ("active", "Active"),
            ("expired", "Expirée"),
            ("blocked", "Bloquée"),
            ("cancelled", "Annulée"),
        ],
        string="État",
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )

    # ==========================================================
    # BLOCAGE
    # ==========================================================

    blocked_date = fields.Date(
        string="Date de blocage",
        readonly=True,
        tracking=True,
    )

    blocked_reason = fields.Text(
        string="Motif du blocage",
        tracking=True,
    )

    # ==========================================================
    # ANNULATION
    # ==========================================================

    cancellation_date = fields.Date(
        string="Date d'annulation",
        readonly=True,
        tracking=True,
    )

    cancellation_reason = fields.Text(
        string="Motif d'annulation",
        tracking=True,
    )

    # ==========================================================
    # RENOUVELLEMENT
    # ==========================================================

    previous_card_id = fields.Many2one(
        comodel_name="association.card",
        string="Carte précédente",
        readonly=True,
        copy=False,
        ondelete="set null",
    )

    renewed_card_id = fields.Many2one(
        comodel_name="association.card",
        string="Nouvelle carte",
        readonly=True,
        copy=False,
        ondelete="set null",
    )

    renewal_count = fields.Integer(
        string="Renouvellements",
        compute="_compute_renewal_count",
    )

    # ==========================================================
    # NOTES
    # ==========================================================

    note = fields.Html(
        string="Notes internes",
    )

    # ==========================================================
    # CONTRAINTES SQL
    # ==========================================================

    _sql_constraints = [
        (
            "association_card_number_unique",
            "unique(card_number)",
            "Le numéro de carte doit être unique.",
        ),
        (
            "association_card_validity_positive",
            "CHECK(validity_months > 0)",
            "La durée de validité doit être supérieure à zéro.",
        ),
    ]

    # ==========================================================
    # CRÉATION
    # ==========================================================

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]

        for vals in vals_list:
            if vals.get("card_number", "Nouveau") == "Nouveau":
                vals["card_number"] = (
                    sequence.next_by_code("association.card")
                    or _("Nouveau")
                )

        return super().create(vals_list)

    # ==========================================================
    # NOM D'AFFICHAGE
    # ==========================================================

    @api.depends(
        "card_number",
        "member_id",
    )
    def _compute_name(self):
        for record in self:
            if record.member_id:
                record.name = "%s - %s" % (
                    record.card_number or "",
                    record.member_id.name or "",
                )
            else:
                record.name = record.card_number or _("Nouvelle carte")

    # ==========================================================
    # DATE D'EXPIRATION
    # ==========================================================

    @api.depends(
        "issue_date",
        "validity_months",
    )
    def _compute_expiry_date(self):
        for record in self:
            if record.issue_date and record.validity_months:
                record.expiry_date = (
                    record.issue_date
                    + relativedelta(
                        months=record.validity_months
                    )
                )
            else:
                record.expiry_date = False

    # ==========================================================
    # INFORMATIONS DE VALIDITÉ
    # ==========================================================

    @api.depends(
        "expiry_date",
        "state",
    )
    def _compute_card_information(self):
        today = fields.Date.context_today(self)

        for record in self:
            record.remaining_days = 0
            record.is_expired = False

            if not record.expiry_date:
                continue

            remaining_days = (
                record.expiry_date - today
            ).days

            record.remaining_days = max(
                remaining_days,
                0,
            )

            record.is_expired = (
                record.expiry_date < today
            )

    # ==========================================================
    # RENOUVELLEMENTS
    # ==========================================================

    def _compute_renewal_count(self):
        Card = self.env["association.card"]

        for record in self:
            record.renewal_count = Card.search_count([
                ("previous_card_id", "=", record.id),
            ])

    # ==========================================================
    # CONTRAINTES MÉTIER
    # ==========================================================

    @api.constrains(
        "member_id",
        "company_id",
    )
    def _check_member_company(self):
        for record in self:
            if (
                record.member_id
                and record.company_id
                and record.member_id.company_id
                != record.company_id
            ):
                raise ValidationError(
                    _(
                        "Le membre et la carte doivent appartenir "
                        "à la même Filiale."
                    )
                )

    @api.constrains(
        "issue_date",
        "expiry_date",
    )
    def _check_card_dates(self):
        for record in self:
            if (
                record.issue_date
                and record.expiry_date
                and record.expiry_date
                <= record.issue_date
            ):
                raise ValidationError(
                    _(
                        "La date d'expiration doit être postérieure "
                        "à la date d'émission."
                    )
                )

    # ==========================================================
    # ÉMISSION
    # ==========================================================

    def action_issue(self):
        Card = self.env["association.card"]

        for record in self:
            if record.state != "draft":
                raise ValidationError(
                    _(
                        "Seule une carte en brouillon "
                        "peut être émise."
                    )
                )

            active_card = Card.search(
                [
                    ("member_id", "=", record.member_id.id),
                    ("state", "=", "active"),
                    ("id", "!=", record.id),
                ],
                limit=1,
            )

            if active_card:
                raise ValidationError(
                    _(
                        "Le membre %(member)s possède déjà "
                        "une carte active : %(card)s."
                    )
                    % {
                        "member": record.member_id.name,
                        "card": active_card.card_number,
                    }
                )

            record.write({
                "state": "active",
                "blocked_date": False,
                "blocked_reason": False,
                "cancellation_date": False,
                "cancellation_reason": False,
            })

        return True

    # ==========================================================
    # BLOQUER
    # ==========================================================

    def action_block(self):
        today = fields.Date.context_today(self)

        for record in self:
            if record.state != "active":
                raise ValidationError(
                    _(
                        "Seule une carte active "
                        "peut être bloquée."
                    )
                )

            if not record.blocked_reason:
                raise ValidationError(
                    _(
                        "Veuillez renseigner le motif "
                        "du blocage avant de bloquer la carte."
                    )
                )

            record.write({
                "state": "blocked",
                "blocked_date": today,
            })

        return True

    # ==========================================================
    # RÉACTIVER
    # ==========================================================

    def action_reactivate(self):
        Card = self.env["association.card"]

        for record in self:
            if record.state != "blocked":
                raise ValidationError(
                    _(
                        "Seule une carte bloquée "
                        "peut être réactivée."
                    )
                )

            active_card = Card.search(
                [
                    ("member_id", "=", record.member_id.id),
                    ("state", "=", "active"),
                    ("id", "!=", record.id),
                ],
                limit=1,
            )

            if active_card:
                raise ValidationError(
                    _(
                        "Impossible de réactiver cette carte.\n\n"
                        "Le membre possède déjà une autre "
                        "carte active : %(card)s."
                    )
                    % {
                        "card": active_card.card_number,
                    }
                )

            if record.is_expired:
                raise ValidationError(
                    _(
                        "Cette carte est expirée et ne peut "
                        "plus être réactivée."
                    )
                )

            record.write({
                "state": "active",
                "blocked_date": False,
                "blocked_reason": False,
            })

        return True

    # ==========================================================
    # EXPIRER
    # ==========================================================

    def action_expire(self):
        for record in self:
            if record.state not in (
                "active",
                "blocked",
            ):
                raise ValidationError(
                    _(
                        "Seule une carte active ou bloquée "
                        "peut être marquée comme expirée."
                    )
                )

            record.write({
                "state": "expired",
            })

        return True

    # ==========================================================
    # ANNULER
    # ==========================================================

    def action_cancel(self):
        today = fields.Date.context_today(self)

        for record in self:
            if record.state == "cancelled":
                continue

            if not record.cancellation_reason:
                raise ValidationError(
                    _(
                        "Veuillez renseigner le motif "
                        "d'annulation avant d'annuler la carte."
                    )
                )

            record.write({
                "state": "cancelled",
                "cancellation_date": today,
            })

        return True

    # ==========================================================
    # RENOUVELER
    # ==========================================================

    def action_renew(self):
        self.ensure_one()

        if self.state not in (
            "expired",
            "blocked",
            "active",
        ):
            raise ValidationError(
                _(
                    "Cette carte ne peut pas être renouvelée "
                    "dans son état actuel."
                )
            )

        if self.renewed_card_id:
            return {
                "type": "ir.actions.act_window",
                "name": _("Carte renouvelée"),
                "res_model": "association.card",
                "res_id": self.renewed_card_id.id,
                "view_mode": "form",
                "target": "current",
            }

        new_card = self.create({
            "member_id": self.member_id.id,
            "company_id": self.company_id.id,
            "issue_date": fields.Date.context_today(self),
            "validity_months": self.validity_months,
            "previous_card_id": self.id,
            "note": _(
                "<p>Carte créée suite au renouvellement "
                "de la carte <strong>%s</strong>.</p>"
            )
            % self.card_number,
        })

        self.write({
            "renewed_card_id": new_card.id,
        })

        return {
            "type": "ir.actions.act_window",
            "name": _("Nouvelle carte"),
            "res_model": "association.card",
            "res_id": new_card.id,
            "view_mode": "form",
            "target": "current",
        }

    # ==========================================================
    # VOIR LE MEMBRE
    # ==========================================================

    def action_view_member(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Membre"),
            "res_model": "association.member",
            "res_id": self.member_id.id,
            "view_mode": "form",
            "target": "current",
        }

    # ==========================================================
    # VOIR LES RENOUVELLEMENTS
    # ==========================================================

    def action_view_renewals(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Historique des cartes"),
            "res_model": "association.card",
            "view_mode": "list,form",
            "domain": [
                "|",
                ("id", "=", self.id),
                ("previous_card_id", "=", self.id),
            ],
            "context": {
                "default_member_id": self.member_id.id,
                "default_company_id": self.company_id.id,
            },
        }
    # ==========================================================
    # ACTION - IMPRIMER LA CARTE MEMBRE
    # ==========================================================

    def action_print_member_card(self):
        self.ensure_one()

        report_action = self.env.ref(
            "primetech_association.action_report_member_card",
            raise_if_not_found=False,
        )

        if not report_action:
            raise UserError(
                _(
                    "Le rapport de carte membre n'est pas "
                    "disponible. Vérifiez la configuration "
                    "du rapport."
                )
            )

        return report_action.report_action(self)