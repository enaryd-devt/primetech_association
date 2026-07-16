# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class AssociationPenalty(models.Model):
    _name = "association.penalty"
    _description = "Sanction ou incident disciplinaire"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "incident_date desc, id desc"

    # ==========================================================
    # IDENTIFICATION
    # ==========================================================

    name = fields.Char(
        string="Référence",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("Nouveau"),
        tracking=True,
    )

    active = fields.Boolean(
        string="Actif",
        default=True,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Filiale",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
        index=True,
    )

    # ==========================================================
    # RÉUNION
    # ==========================================================

    meeting_id = fields.Many2one(
        comodel_name="association.meeting",
        string="Réunion",
        required=True,
        ondelete="restrict",
        tracking=True,
        index=True,
    )

    meeting_date = fields.Date(
        related="meeting_id.meeting_date",
        string="Date de réunion",
        readonly=True,
        store=True,
        index=True,
    )

    meeting_type = fields.Selection(
        related="meeting_id.meeting_type",
        string="Type de réunion",
        readonly=True,
        store=True,
    )

    # ==========================================================
    # MEMBRE
    # ==========================================================

    member_id = fields.Many2one(
        comodel_name="association.member",
        string="Membre concerné",
        required=True,
        ondelete="restrict",
        tracking=True,
        index=True,
    )

    member_code = fields.Char(
        related="member_id.member_code",
        string="Code membre",
        readonly=True,
        store=True,
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

    # ==========================================================
    # INCIDENT
    # ==========================================================

    incident_date = fields.Datetime(
        string="Date et heure de l'incident",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
        index=True,
    )

    incident_type = fields.Selection(
        selection=[
            ("disturbance", "Trouble de séance"),
            ("late", "Retard"),
            ("indiscipline", "Indiscipline"),
            ("unjustified_absence", "Absence injustifiée"),
            ("rule_violation", "Non-respect du règlement"),
            ("decision_refusal", "Refus d'exécuter une décision"),
            ("inappropriate_words", "Propos déplacés"),
            ("misconduct", "Mauvaise conduite"),
            ("other", "Autre"),
        ],
        string="Type d'incident",
        required=True,
        tracking=True,
        index=True,
    )

    incident_description = fields.Text(
        string="Description des faits",
        tracking=True,
    )

    # ==========================================================
    # GRAVITÉ
    # ==========================================================

    severity = fields.Selection(
        selection=[
            ("minor", "Mineure"),
            ("low", "Faible"),
            ("medium", "Moyenne"),
            ("serious", "Grave"),
            ("critical", "Très grave"),
        ],
        string="Niveau de gravité",
        required=True,
        default="low",
        tracking=True,
        index=True,
    )

    # ==========================================================
    # SANCTION
    # ==========================================================

    penalty_type = fields.Selection(
        selection=[
            ("observation", "Observation"),
            ("warning", "Avertissement"),
            ("fine", "Sanction financière"),
            ("apology", "Présentation d'excuses"),
            ("corrective_action", "Action corrective"),
            ("suspension", "Suspension"),
            ("exclusion", "Exclusion"),
            ("other", "Autre"),
        ],
        string="Type de sanction",
        required=True,
        default="observation",
        tracking=True,
        index=True,
    )

    penalty_description = fields.Text(
        string="Décision disciplinaire",
        tracking=True,
    )

    # ==========================================================
    # SANCTION FINANCIÈRE
    # ==========================================================

    amount = fields.Monetary(
        string="Montant de la sanction",
        currency_field="currency_id",
        tracking=True,
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        string="Devise",
        readonly=True,
        store=True,
    )

    amount_paid = fields.Monetary(
        string="Montant payé",
        currency_field="currency_id",
        default=0.0,
        readonly=True,
        tracking=True,
    )

    amount_remaining = fields.Monetary(
        string="Reste à payer",
        currency_field="currency_id",
        compute="_compute_amount_remaining",
        store=True,
    )

    # ==========================================================
    # SUSPENSION
    # ==========================================================

    suspension_days = fields.Integer(
        string="Durée de suspension (jours)",
        tracking=True,
    )

    # ==========================================================
    # ACTION CORRECTIVE
    # ==========================================================

    corrective_action_required = fields.Boolean(
        string="Action requise pour lever la sanction",
        default=False,
        tracking=True,
    )

    corrective_action = fields.Text(
        string="Action à accomplir",
        tracking=True,
        help=(
            "Action que le membre doit accomplir "
            "pour permettre la levée de la sanction."
        ),
    )

    corrective_deadline = fields.Date(
        string="Date limite",
        tracking=True,
    )

    corrective_action_done = fields.Boolean(
        string="Action accomplie",
        default=False,
        readonly=True,
        tracking=True,
    )

    corrective_action_date = fields.Datetime(
        string="Date d'accomplissement",
        readonly=True,
        tracking=True,
    )

    corrective_action_note = fields.Text(
        string="Observation sur l'action réalisée",
        tracking=True,
    )

    # ==========================================================
    # LEVÉE DE SANCTION
    # ==========================================================

    lifted_by = fields.Many2one(
        comodel_name="res.users",
        string="Sanction levée par",
        readonly=True,
        tracking=True,
    )

    lifted_date = fields.Datetime(
        string="Date de levée",
        readonly=True,
        tracking=True,
    )

    lift_reason = fields.Text(
        string="Motif de levée",
        readonly=True,
        tracking=True,
    )

    # ==========================================================
    # ANNULATION
    # ==========================================================

    cancelled_by = fields.Many2one(
        comodel_name="res.users",
        string="Annulée par",
        readonly=True,
        tracking=True,
    )

    cancellation_date = fields.Datetime(
        string="Date d'annulation",
        readonly=True,
        tracking=True,
    )

    cancellation_reason = fields.Text(
        string="Motif d'annulation",
        tracking=True,
    )

    # ==========================================================
    # PROCÈS-VERBAL
    # ==========================================================

    include_in_minutes = fields.Boolean(
        string="Inclure dans le procès-verbal",
        default=True,
        tracking=True,
    )

    minutes_note = fields.Text(
        string="Mention au procès-verbal",
    )

    # ==========================================================
    # VALIDATION
    # ==========================================================

    state = fields.Selection(
        selection=[
            ("draft", "Brouillon"),
            ("validated", "Validée"),
            ("executed", "Exécutée"),
            ("lifted", "Levée"),
            ("cancelled", "Annulée"),
        ],
        string="Statut",
        required=True,
        default="draft",
        tracking=True,
        index=True,
    )

    validated_by = fields.Many2one(
        comodel_name="res.users",
        string="Validée par",
        readonly=True,
        tracking=True,
    )

    validation_date = fields.Datetime(
        string="Date de validation",
        readonly=True,
        tracking=True,
    )

    executed_date = fields.Datetime(
        string="Date d'exécution",
        readonly=True,
        tracking=True,
    )

    note = fields.Html(
        string="Observations internes",
    )

    # ==========================================================
    # CALCUL DU RESTE
    # ==========================================================

    @api.depends(
        "amount",
        "amount_paid",
    )
    def _compute_amount_remaining(self):

        for record in self:

            record.amount_remaining = max(
                record.amount - record.amount_paid,
                0.0,
            )

    # ==========================================================
    # CRÉATION
    # ==========================================================

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            if vals.get("name", _("Nouveau")) == _("Nouveau"):

                vals["name"] = (
                    self.env["ir.sequence"].next_by_code(
                        "association.penalty"
                    )
                    or _("Nouveau")
                )

        return super().create(vals_list)

    # ==========================================================
    # VALIDER
    # ==========================================================

    def action_validate(self):

        for record in self:

            if record.state != "draft":

                raise UserError(
                    _(
                        "Seule une sanction en brouillon "
                        "peut être validée."
                    )
                )

            if not record.member_id:

                raise UserError(
                    _("Veuillez sélectionner le membre concerné.")
                )

            if not record.incident_type:

                raise UserError(
                    _("Veuillez sélectionner le type d'incident.")
                )

            if not record.incident_description:

                raise UserError(
                    _("Veuillez décrire précisément les faits.")
                )

            if not record.severity:

                raise UserError(
                    _("Veuillez définir le niveau de gravité.")
                )

            if not record.penalty_type:

                raise UserError(
                    _("Veuillez définir le type de sanction.")
                )

            if not record.penalty_description:

                raise UserError(
                    _(
                        "Veuillez renseigner la décision "
                        "disciplinaire."
                    )
                )

            if (
                record.penalty_type == "fine"
                and record.amount <= 0
            ):

                raise UserError(
                    _(
                        "Veuillez saisir le montant "
                        "de la sanction financière."
                    )
                )

            if (
                record.penalty_type == "suspension"
                and record.suspension_days <= 0
            ):

                raise UserError(
                    _(
                        "Veuillez renseigner la durée "
                        "de suspension."
                    )
                )

            if (
                record.corrective_action_required
                and not record.corrective_action
            ):

                raise UserError(
                    _(
                        "Veuillez définir l'action que le membre "
                        "doit accomplir pour lever la sanction."
                    )
                )

            record.write(
                {
                    "state": "validated",
                    "validated_by": self.env.user.id,
                    "validation_date": fields.Datetime.now(),
                }
            )

            record.message_post(
                body=_(
                    "Sanction validée par %s."
                )
                % self.env.user.display_name
            )

        return True

    # ==========================================================
    # MARQUER L'ACTION CORRECTIVE COMME ACCOMPLIE
    # ==========================================================

    def action_complete_corrective_action(self):

        for record in self:

            if record.state not in (
                "validated",
                "executed",
            ):

                raise UserError(
                    _(
                        "L'action corrective ne peut être "
                        "enregistrée que pour une sanction validée."
                    )
                )

            if not record.corrective_action_required:

                raise UserError(
                    _(
                        "Aucune action corrective n'est définie "
                        "pour cette sanction."
                    )
                )

            record.write(
                {
                    "corrective_action_done": True,
                    "corrective_action_date": fields.Datetime.now(),
                }
            )

            record.message_post(
                body=_(
                    "L'action corrective demandée au membre "
                    "a été marquée comme accomplie."
                )
            )

        return True

    # ==========================================================
    # EXÉCUTER
    # ==========================================================

    def action_execute(self):

        for record in self:

            if record.state != "validated":

                raise UserError(
                    _(
                        "Seule une sanction validée "
                        "peut être exécutée."
                    )
                )

            record.write(
                {
                    "state": "executed",
                    "executed_date": fields.Datetime.now(),
                }
            )

        return True

    # ==========================================================
    # LEVER LA SANCTION
    # ==========================================================

    def action_lift(self):

        for record in self:

            if record.state not in (
                "validated",
                "executed",
            ):

                raise UserError(
                    _(
                        "Seule une sanction validée ou exécutée "
                        "peut être levée."
                    )
                )

            if (
                record.corrective_action_required
                and not record.corrective_action_done
            ):

                raise UserError(
                    _(
                        "Impossible de lever la sanction.\n\n"
                        "Le membre n'a pas encore accompli "
                        "l'action corrective demandée."
                    )
                )

            if (
                record.penalty_type == "fine"
                and record.amount_remaining > 0
            ):

                raise UserError(
                    _(
                        "Impossible de lever la sanction.\n\n"
                        "Le montant de la sanction financière "
                        "n'est pas entièrement réglé.\n\n"
                        "Reste à payer : %s %s"
                    )
                    % (
                        record.amount_remaining,
                        record.currency_id.symbol or "",
                    )
                )

            if not record.lift_reason:

                raise UserError(
                    _(
                        "Veuillez renseigner le motif "
                        "de levée de la sanction."
                    )
                )

            record.write(
                {
                    "state": "lifted",
                    "lifted_by": self.env.user.id,
                    "lifted_date": fields.Datetime.now(),
                }
            )

            record.message_post(
                body=_(
                    "Sanction levée par %s."
                )
                % self.env.user.display_name
            )

        return True

    # ==========================================================
    # ANNULER
    # ==========================================================

    def action_cancel(self):

        for record in self:

            if record.state not in (
                "draft",
                "validated",
            ):

                raise UserError(
                    _(
                        "Cette sanction ne peut plus "
                        "être annulée."
                    )
                )

            if not record.cancellation_reason:

                raise UserError(
                    _(
                        "Veuillez renseigner le motif "
                        "d'annulation de la sanction."
                    )
                )

            record.write(
                {
                    "state": "cancelled",
                    "cancelled_by": self.env.user.id,
                    "cancellation_date": fields.Datetime.now(),
                }
            )

            record.message_post(
                body=_(
                    "Sanction annulée par %s."
                )
                % self.env.user.display_name
            )

        return True

    # ==========================================================
    # SUPPRESSION
    # ==========================================================

    def unlink(self):

        for record in self:

            if record.state != "draft":

                raise UserError(
                    _(
                        "Seules les sanctions en brouillon "
                        "peuvent être supprimées."
                    )
                )
        self._check_meeting_not_closed()

        return super().unlink()
    
    def _check_meeting_not_closed(self):

        closed_records = self.filtered(
            lambda record:
                record.meeting_id
                and record.meeting_id.state == "closed"
        )

        if closed_records:

            raise UserError(
                _(
                    "La réunion est terminée et verrouillée.\n\n"
                    "Cette information ne peut plus "
                    "être modifiée."
                )
            )
        
    def write(self, vals):

        self._check_meeting_not_closed()

        return super().write(vals)