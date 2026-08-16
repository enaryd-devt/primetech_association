# -*- coding: utf-8 -*-
##############################################################################
#
# PrimeTech Association Management
#
# Copyright (C) 2026 PrimeTech Services
#
# LGPL-3
#
##############################################################################

from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AssociationMember(models.Model):
    _name = "association.member"
    _description = "Association Member"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
    ]
    _order = "member_code desc"

    # ==========================================================
    # TECHNIQUE
    # ==========================================================

    active = fields.Boolean(
        string="Actif",
        default=True,
        tracking=True,
        index=True,
    )

    sequence = fields.Integer(
        string="Séquence",
        default=10,
    )

    color = fields.Integer(
        string="Couleur",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Filiale",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )

    currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Devise",
        store=True,
        readonly=True,
    )

    # ==========================================================
    # IDENTIFICATION
    # ==========================================================

    member_code = fields.Char(
        string="Code membre",
        copy=False,
        readonly=True,
        default=lambda self: _("Nouveau"),
        tracking=True,
        index=True,
    )

    membership_number = fields.Char(
        string="Numéro d'adhésion",
        tracking=True,
        copy=False,
        index=True,
    )

    first_name = fields.Char(
        string="Prénom",
        required=True,
        tracking=True,
    )

    last_name = fields.Char(
        string="Nom",
        required=True,
        tracking=True,
    )

    name = fields.Char(
        string="Nom complet",
        compute="_compute_name",
        store=True,
        tracking=True,
        index=True,
    )

    gender = fields.Selection(
        [
            ("male", "Masculin"),
            ("female", "Féminin"),
        ],
        string="Sexe",
        tracking=True,
    )

    birth_date = fields.Date(
        string="Date de naissance",
        tracking=True,
    )

    birth_place = fields.Char(
        string="Lieu de naissance",
    )

    nationality_id = fields.Many2one(
        "res.country",
        string="Nationalité",
    )

    marital_status = fields.Selection(
        [
            ("single", "Célibataire"),
            ("married", "Marié(e)"),
            ("divorced", "Divorcé(e)"),
            ("widowed", "Veuf / Veuve"),
        ],
        string="Situation matrimoniale",
    )

    profession = fields.Char(
        string="Profession",
    )

    image_1920 = fields.Image(
        string="Photo",
    )

    image_1024 = fields.Image(
        related="image_1920",
        string="Photo 1024",
        max_width=1024,
        max_height=1024,
        store=True,
    )

    image_512 = fields.Image(
        related="image_1920",
        string="Photo 512",
        max_width=512,
        max_height=512,
        store=True,
    )

    image_256 = fields.Image(
        related="image_1920",
        string="Photo 256",
        max_width=256,
        max_height=256,
        store=True,
    )

    image_128 = fields.Image(
        related="image_1920",
        string="Photo",
        max_width=128,
        max_height=128,
        store=True,
    )

    # ==========================================================
    # COORDONNÉES
    # ==========================================================

    phone = fields.Char(
        string="Téléphone",
        tracking=True,
    )

    mobile = fields.Char(
        string="Téléphone mobile",
        tracking=True,
    )

    whatsapp = fields.Char(
        string="WhatsApp",
    )

    email = fields.Char(
        string="Adresse e-mail",
        tracking=True,
    )

    website = fields.Char(
        string="Site web",
    )

    street = fields.Char(
        string="Adresse",
    )

    street2 = fields.Char(
        string="Complément d'adresse",
    )

    city = fields.Char(
        string="Ville",
    )

    zip = fields.Char(
        string="Code postal",
    )

    state_id = fields.Many2one(
        "res.country.state",
        string="Région / État",
    )

    country_id = fields.Many2one(
        "res.country",
        string="Pays",
    )

    # ==========================================================
    # ASSOCIATION
    # ==========================================================

    join_date = fields.Date(
        string="Date d'adhésion",
        tracking=True,
    )

    years_of_membership = fields.Integer(
        string="Ancienneté",
        compute="_compute_years_of_membership",
        store=True,
    )

    category_id = fields.Many2one(
        "association.member.category",
        string="Catégorie",
        tracking=True,
        ondelete="restrict",
        index=True,
    )

    function_id = fields.Many2one(
        "association.member.function",
        string="Fonction",
        default=lambda self: self._default_member_function(),
        tracking=True,
        ondelete="restrict",
        index=True,
    )

    committee_id = fields.Many2one(
        "association.committee",
        string="Bureau exécutif",
        ondelete="set null",
    )

    @api.model
    def _default_member_function(self):
        """Return the ordinary Member function for the current company."""
        function = self.env["association.member.function"].search(
            [
                ("name", "=ilike", "Membre"),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )
        return function or self.env.ref(
            "primetech_association.member_function_member",
            raise_if_not_found=False,
        )

    state = fields.Selection(
        selection=[
            ("draft", "Brouillon"),
            ("active", "Actif"),
            ("suspended", "Suspendu"),
            ("resigned", "Démissionnaire"),
            ("excluded", "Exclu"),
        ],
        string="Statut",
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )

    # ==========================================================
    # INFORMATIONS PROFESSIONNELLES
    # ==========================================================

    company_name = fields.Char(
        string="Entreprise",
    )

    job_title = fields.Char(
        string="Poste occupé",
    )

    company_phone = fields.Char(
        string="Téléphone de l'entreprise",
    )

    company_email = fields.Char(
        string="E-mail de l'entreprise",
    )

    company_website = fields.Char(
        string="Site web de l'entreprise",
    )

    company_address = fields.Text(
        string="Adresse de l'entreprise",
    )

    # ==========================================================
    # COMPTE FINANCIER MEMBRE
    # ==========================================================

    wallet_id = fields.Many2one(
        comodel_name="association.member.wallet",
        string="Compte financier",
        compute="_compute_wallet_information",
    )

    wallet_balance = fields.Monetary(
        string="Solde du compte",
        currency_field="currency_id",
        compute="_compute_wallet_information",
    )

    wallet_transaction_count = fields.Integer(
        string="Mouvements du compte",
        compute="_compute_wallet_information",
    )


    # ==========================================================
    # MOUVEMENTS DU COMPTE MEMBRE
    # ==========================================================

    def action_view_transactions(self):

        self.ensure_one()

        Wallet = self.env[
            "association.member.wallet"
        ]

        wallet = Wallet.search(
            [
                (
                    "member_id",
                    "=",
                    self.id,
                ),
                (
                    "company_id",
                    "=",
                    self.company_id.id,
                ),
            ],
            limit=1,
        )

        if not wallet:

            wallet = Wallet.create(
                {
                    "member_id":
                        self.id,

                    "company_id":
                        self.company_id.id,
                }
            )

        return {
            "type":
                "ir.actions.act_window",

            "name":
                _(
                    "Mouvements du compte - %s"
                )
                % self.display_name,

            "res_model":
                "association.member.wallet.transaction",

            "view_mode":
                "list,form",

            "domain": [
                (
                    "wallet_id",
                    "=",
                    wallet.id,
                ),
            ],

            "context": {
                "default_wallet_id":
                    wallet.id,

                "default_member_id":
                    self.id,

                "create":
                    False,

                "delete":
                    False,
            },

            "target":
                "current",
        }


    def _compute_wallet_information(self):

        Wallet = self.env["association.member.wallet"]

        for record in self:

            wallet = Wallet.search(
                [
                    ("member_id", "=", record.id),
                ],
                limit=1,
            )

            record.wallet_id = wallet

            record.wallet_balance = (
                wallet.balance
                if wallet
                else 0.0
            )

            record.wallet_transaction_count = (
                wallet.transaction_count
                if wallet
                else 0
            )


    def _get_or_create_wallet(self):

        self.ensure_one()

        Wallet = self.env["association.member.wallet"]

        wallet = Wallet.search(
            [
                ("member_id", "=", self.id),
            ],
            limit=1,
        )

        if not wallet:

            wallet = Wallet.create(
                {
                    "member_id": self.id,
                }
            )

        return wallet


    def action_view_wallet(self):

        self.ensure_one()

        wallet = self._get_or_create_wallet()

        return {
            "type": "ir.actions.act_window",
            "name": _("Compte financier"),
            "res_model": "association.member.wallet",
            "res_id": wallet.id,
            "view_mode": "form",
            "target": "current",
        }

    # ==========================================================
    # CARTE DE MEMBRE
    # ==========================================================

    card_number = fields.Char(
        string="Numéro de carte",
        copy=False,
        index=True,
    )

    card_issue_date = fields.Date(
        string="Date de délivrance",
    )

    card_expiration_date = fields.Date(
        string="Date d'expiration",
    )

    card_state = fields.Selection(
        [
            ("draft", "Brouillon"),
            ("valid", "Valide"),
            ("expired", "Expirée"),
            ("cancelled", "Annulée"),
        ],
        string="Statut de la carte",
        default="draft",
        tracking=True,
    )

    # ==========================================================
    # SANTÉ
    # ==========================================================

    blood_group = fields.Selection(
        [
            ("A+", "A+"),
            ("A-", "A-"),
            ("B+", "B+"),
            ("B-", "B-"),
            ("AB+", "AB+"),
            ("AB-", "AB-"),
            ("O+", "O+"),
            ("O-", "O-"),
        ],
        string="Groupe sanguin",
    )

    allergies = fields.Text(
        string="Allergies",
    )

    chronic_disease = fields.Text(
        string="Maladies chroniques",
    )

    doctor_name = fields.Char(
        string="Médecin traitant",
    )

    doctor_phone = fields.Char(
        string="Téléphone du médecin",
    )

    # ==========================================================
    # DOCUMENTS
    # ==========================================================

    id_card_number = fields.Char(
        string="Numéro de CNI",
    )

    passport_number = fields.Char(
        string="Numéro de passeport",
    )

    driving_license = fields.Char(
        string="Numéro de permis de conduire",
    )

    id_card_front = fields.Image(
        string="Recto de la CNI",
    )

    id_card_back = fields.Image(
        string="Verso de la CNI",
    )

    passport_scan = fields.Image(
        string="Copie du passeport",
    )

    signature_scan = fields.Image(
        string="Signature",
    )

    # ==========================================================
    # RÉSEAUX SOCIAUX
    # ==========================================================

    facebook = fields.Char(
        string="Facebook",
    )

    instagram = fields.Char(
        string="Instagram",
    )

    linkedin = fields.Char(
        string="LinkedIn",
    )

    twitter = fields.Char(
        string="X / Twitter",
    )

    telegram = fields.Char(
        string="Telegram",
    )

    youtube = fields.Char(
        string="YouTube",
    )

    # ==========================================================
    # COMPÉTENCES
    # ==========================================================

    language = fields.Char(
        string="Langues parlées",
    )

    skill_ids = fields.Many2many(
        "association.skill",
        string="Compétences",
    )

    # ==========================================================
    # NOTES
    # ==========================================================

    note = fields.Html(
        string="Notes internes",
    )

    # ==========================================================
    # STATISTICS
    # ==========================================================

    subscription_count = fields.Integer(
        string="Subscriptions",
        compute="_compute_statistics",
    )

    payment_count = fields.Integer(
        string="Payments",
        compute="_compute_statistics",
    )

    meeting_count = fields.Integer(
        string="Meetings",
        compute="_compute_statistics",
    )

    attendance_count = fields.Integer(
        string="Attendances",
        compute="_compute_statistics",
    )

    donation_count = fields.Integer(
        string="Donations",
        compute="_compute_statistics",
    )

    penalty_count = fields.Integer(
        string="Penalties",
        compute="_compute_statistics",
    )


    balance = fields.Monetary(
        string="Solde du compte",
        currency_field="currency_id",
        compute="_compute_real_account_balance",
        store=False,
    )

    # ==========================================================
    # COMPUTE
    # ==========================================================

    # ==========================================================
    # ACTION - OUVRIR LES MOUVEMENTS DU COMPTE MEMBRE
    # ==========================================================

    def action_view_member_account_transactions(self):
        self.ensure_one()

        Account = self.env[
            "association.member.account"
        ]

        domain = [
            (
                "member_id",
                "=",
                self.id,
            ),
        ]

        if self.company_id:
            domain.append(
                (
                    "company_id",
                    "=",
                    self.company_id.id,
                )
            )

        account = Account.search(
            domain,
            limit=1,
        )

        # ======================================================
        # AUCUN COMPTE
        # ======================================================

        if not account:
            return {
                "type": "ir.actions.act_window",
                "name": "Mouvements du compte",
                "res_model":
                    "association.member.account.transaction",
                "view_mode": "list,form",
                "domain": [
                    (
                        "id",
                        "=",
                        0,
                    ),
                ],
                "context": {
                    "create": False,
                },
            }

        # ======================================================
        # OUVERTURE DES MOUVEMENTS DU COMPTE RÉEL
        # ======================================================

        return {
            "type": "ir.actions.act_window",
            "name": "Mouvements - %s"
                % self.display_name,
            "res_model":
                "association.member.account.transaction",
            "view_mode": "list,form",
            "domain": [
                (
                    "account_id",
                    "=",
                    account.id,
                ),
            ],
            "context": {
                "default_account_id": account.id,
                "search_default_account_id": account.id,
                "create": False,
            },
            "target": "current",
        }
    
    
    @api.depends("function_id")
    def _compute_is_executive(self):
        for rec in self:
            rec.is_executive = bool(
                rec.function_id and rec.function_id.executive_member
            )@api.depends("first_name", "last_name")
    
    def _compute_name(self):
        for rec in self:
            rec.name = " ".join(
                filter(None, [rec.first_name, rec.last_name])
            )

    @api.depends("join_date")
    def _compute_years_of_membership(self):
        today = fields.Date.today()

        for rec in self:

            rec.years_of_membership = 0

            if rec.join_date:
                rec.years_of_membership = (
                    today.year - rec.join_date.year
                )

    def _compute_statistics(self):
        SubscriptionLine = self.env["association.subscription.line"]
        Payment = self.env["association.payment"]
        Meeting = self.env["association.meeting"]
        Attendance = self.env["association.attendance"]
        Donation = self.env["association.donation"]
        Penalty = self.env["association.penalty"]

        for rec in self:
            if not rec.id:
                rec.subscription_count = 0
                rec.payment_count = 0
                rec.meeting_count = 0
                rec.attendance_count = 0
                rec.donation_count = 0
                rec.penalty_count = 0
            
                continue

            # ----------------------------------------------------------
            # SUBSCRIPTIONS
            # ----------------------------------------------------------

            subscription_lines = SubscriptionLine.search([
                ("member_id", "=", rec.id)
            ])

            rec.subscription_count = len(
                subscription_lines.mapped("subscription_id")
            )

            # ----------------------------------------------------------
            # PAYMENTS
            # ----------------------------------------------------------

            payments = Payment.search([
                ("member_id", "=", rec.id)
            ])

            rec.payment_count = len(payments)

            # ----------------------------------------------------------
            # MEETINGS
            # ----------------------------------------------------------

            attendances = Attendance.search([
                ("member_id", "=", rec.id)
            ])

            rec.attendance_count = len(attendances)

            rec.meeting_count = len(
                attendances.mapped("meeting_id")
            )

        # ----------------------------------------------------------
        # DONATIONS
        # ----------------------------------------------------------

        donations = Donation.search([
            ("member_id", "=", rec.id)
        ])

        rec.donation_count = len(donations)

        # ----------------------------------------------------------
        # PENALTIES
        # ----------------------------------------------------------

        penalties = Penalty.search([
            ("member_id", "=", rec.id)
        ])

        rec.penalty_count = len(penalties)

        # ----------------------------------------------------------
        # BALANCE
        # ----------------------------------------------------------

        total_due = sum(
            subscription_lines.mapped("amount_due")
        )

        total_paid = sum(
            subscription_lines.mapped("amount_paid")
        )

        rec.balance = total_due - total_paid

        
    def _compute_attachment_count(self):

        Attachment = self.env["ir.attachment"]

        for rec in self:

            rec.attachment_count = Attachment.search_count([

                ("res_model", "=", self._name),

                ("res_id", "=", rec.id),

            ])

    # ==========================================================
    # SOLDE RÉEL DU COMPTE MEMBRE
    # ==========================================================

    def _compute_real_account_balance(self):

        Account = self.env[
            "association.member.account"
        ]

        for member in self:

            # ======================================================
            # VALEUR PAR DÉFAUT
            # ======================================================

            member.balance = 0.0

            # ======================================================
            # RECHERCHE DU COMPTE FINANCIER RÉEL
            # ======================================================

            domain = [
                (
                    "member_id",
                    "=",
                    member.id,
                ),
            ]

            if member.company_id:

                domain.append(
                    (
                        "company_id",
                        "=",
                        member.company_id.id,
                    )
                )

            account = Account.search(
                domain,
                limit=1,
            )

            # ======================================================
            # LECTURE DU SOLDE ACTUEL
            # ======================================================

            if account:

                account.invalidate_recordset([
                    "balance",
                ])

                member.balance = (
                    account.balance or 0.0
                )
    
    
    
    @api.depends(
        "phone",
        "mobile",
        "email",
        "birth_date",
        "category_id",
        "function_id",
        "street",
        "city",
        "country_id",
        "image_1920",
    )
    def _compute_completion_rate(self):

        fields_to_check = [

            "phone",

            "mobile",

            "email",

            "birth_date",

            "category_id",

            "function_id",

            "street",

            "city",

            "country_id",

            "image_1920",

        ]

        total = len(fields_to_check)

        for rec in self:

            completed = 0

            for field_name in fields_to_check:

                if rec[field_name]:

                    completed += 1

            rec.completion_rate = int(
                completed * 100 / total
            )

    # ==========================================================
    # CONSTRAINTS
    # ==========================================================

    @api.constrains("email")
    def _check_email(self):

        for rec in self:

            if rec.email:

                duplicate = self.search([

                    ("email", "=", rec.email),

                    ("id", "!=", rec.id),

                ], limit=1)

                if duplicate:

                    raise ValidationError(

                        _("This email already exists.")

                    )

    @api.constrains("member_code")
    def _check_member_code(self):

        for rec in self:

            if rec.member_code == _("New"):

                continue

            duplicate = self.search([

                ("member_code", "=", rec.member_code),

                ("id", "!=", rec.id),

            ], limit=1)

            if duplicate:

                raise ValidationError(

                    _("Duplicate member code.")

                )


    # ==========================================================
    # ORM METHODS
    # ==========================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            # ------------------------------------------------------
            # MEMBER NUMBER
            # ------------------------------------------------------

            if not vals.get("member_code") or vals.get("member_code") == "New":
                vals["member_code"] = (
                    self.env["ir.sequence"].next_by_code(
                        "association.member"
                    )
                    or "New"
                )

            # ------------------------------------------------------
            # MEMBER NAME
            # ------------------------------------------------------

            first_name = (vals.get("first_name") or "").strip()
            last_name = (vals.get("last_name") or "").strip()

            if first_name or last_name:
                vals["name"] = " ".join(
                    part
                    for part in [
                        first_name,
                        last_name,
                    ]
                    if part
                )

            elif vals.get("name"):
                vals["name"] = vals["name"].strip()

        return super().create(vals_list)


    def write(self, vals):

        result = super().write(vals)

        if "first_name" in vals or "last_name" in vals:

            for rec in self:

                first_name = (rec.first_name or "").strip()
                last_name = (rec.last_name or "").strip()

                member_name = " ".join(
                    part
                    for part in [
                        first_name,
                        last_name,
                    ]
                    if part
                )

                if member_name and rec.name != member_name:
                    super(
                        AssociationMember,
                        rec,
                    ).write({
                        "name": member_name,
                    })

        return result
    
    # ==========================================================
    # ACTIONS
    # ==========================================================

    def action_activate(self):
        self.write({"state": "active"})

    def action_suspend(self):
        self.write({"state": "suspended"})

    def action_resign(self):
        self.write({"state": "resigned"})

    def action_deceased(self):
        self.write({"state": "deceased"})

    def action_set_draft(self):
        self.write({"state": "draft"})

    # ==========================================================
    # SMART BUTTON ACTIONS
    # ==========================================================

    def action_view_payments(self):
        """
        Open all payments linked to the current member.
        """
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Payments"),
            "res_model": "association.payment",
            "view_mode": "list,form",
            "domain": [
                ("member_id", "=", self.id),
            ],
            "context": {
                "default_member_id": self.id,
            },
        }

    def action_view_subscriptions(self):
        """
        Open subscriptions linked to the current member
        through association.subscription.line.
        """
        self.ensure_one()

        subscription_lines = self.env[
            "association.subscription.line"
        ].search([
            ("member_id", "=", self.id),
        ])

        subscription_ids = subscription_lines.mapped(
            "subscription_id"
        ).ids

        return {
            "type": "ir.actions.act_window",
            "name": _("Subscriptions"),
            "res_model": "association.subscription",
            "view_mode": "list,form",
            "domain": [
                ("id", "in", subscription_ids),
            ],
            "context": {
                "create": False,
            },
        }

    def action_view_meetings(self):
        """
        Open meetings where the current member
        has an attendance record.
        """
        self.ensure_one()

        attendance_lines = self.env[
            "association.attendance"
        ].search([
            ("member_id", "=", self.id),
        ])

        meeting_ids = attendance_lines.mapped(
            "meeting_id"
        ).ids

        return {
            "type": "ir.actions.act_window",
            "name": _("Meetings"),
            "res_model": "association.meeting",
            "view_mode": "list,form",
            "domain": [
                ("id", "in", meeting_ids),
            ],
            "context": {
                "create": False,
            },
        }

    def action_view_attendances(self):
        """
        Open attendance records linked to the member.
        """
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Attendances"),
            "res_model": "association.attendance",
            "view_mode": "list,form",
            "domain": [
                ("member_id", "=", self.id),
            ],
            "context": {
                "default_member_id": self.id,
            },
        }

    def action_view_donations(self):
        """
        Open donations linked to the current member.
        """
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Donations"),
            "res_model": "association.donation",
            "view_mode": "list,form",
            "domain": [
                ("member_id", "=", self.id),
            ],
            "context": {
                "default_member_id": self.id,
            },
        }

    def action_view_penalties(self):
        """
        Open penalties linked to the current member.
        """
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Penalties"),
            "res_model": "association.penalty",
            "view_mode": "list,form",
            "domain": [
                ("member_id", "=", self.id),
            ],
            "context": {
                "default_member_id": self.id,
            },
        }
    
    # ==========================================================
    # REPORT
    # ==========================================================

    def action_print_member_card(self):

        self.ensure_one()

        return self.env.ref(
            "primetech_association.action_member_card_report"
        ).report_action(self)

    def action_print_member_directory(self):
        return self.env.ref(
            "primetech_association.action_report_member_directory"
        ).report_action(self)

    # ==========================================================
    # MEMBER STATE ACTIONS
    # ==========================================================

    def action_activate(self):
        """
        Activate member.
        """
        for rec in self:
            rec.write({
                "state": "active",
                "active": True,
            })

        return True


    def action_suspend(self):
        """
        Suspend member.
        """
        for rec in self:
            rec.write({
                "state": "suspended",
            })

        return True


    def action_reactivate(self):
        """
        Reactivate suspended member.
        """
        for rec in self:
            rec.write({
                "state": "active",
                "active": True,
            })

        return True


    def action_resign(self):
        """
        Mark member as resigned.
        """
        for rec in self:
            rec.write({
                "state": "resigned",
            })

        return True


    def action_exclude(self):
        """
        Exclude member.
        """
        for rec in self:
            rec.write({
                "state": "excluded",
            })

        return True


    def action_reset_draft(self):
        """
        Reset member to draft.
        """
        for rec in self:
            rec.write({
                "state": "draft",
                "active": True,
            })

        return True
