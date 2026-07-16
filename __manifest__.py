# -*- coding: utf-8 -*-

{
    "name": "PrimeTech Association Management",

    "summary": "Gestion des associations",

    "description": """
PrimeTech Association Management

Gestion des membres
Gestion des cotisations
Gestion des paiements
Gestion des réunions
Gestion des présences
Gestion financière
""",

    "version": "18.0.1.0.0",

    "author": "PrimeTech Services",

    "website": "https://www.primetechafrik.com",

    "category": "Services",

    "license": "LGPL-3",

    "depends": [
        "base",
        "mail",
        "contacts",
        "web",
    ],

    "data": [

        # =====================================================
        # SECURITY
        # =====================================================

        "security/association_security.xml",
        "security/ir.model.access.csv",

        # =====================================================
        # DATA
        # =====================================================

        "data/association_sequence.xml",
        "data/member_category_data.xml",
        "data/member_function_data.xml",
        "data/bank_sequence.xml",

        # =====================================================
        # VIEWS
        # =====================================================

        "views/dashboard_views.xml",

        "views/member_views.xml",
        "views/member_card_views.xml",

        "views/committee_views.xml",

        "views/subscription_views.xml",
        "views/payment_views.xml",
        "views/subscription_period_views.xml",
        "views/donation_views.xml",
        "views/income_views.xml",
        "views/expense_views.xml",
        "views/fund_views.xml",

       

        "views/meeting_views.xml",
        "views/attendance_views.xml",
        "views/penalty_views.xml",
        "views/res_config_settings_views.xml",

        # =====================================================
        # REPORT
        # =====================================================

        "report/member_card_template.xml",
        "report/member_card_report.xml",

        "report/meeting_minutes_report.xml",
        "report/meeting_minutes_template.xml",

        # Banque / Trésorerie
        "views/fund_transaction_views.xml",

        "views/member_category_views.xml",
        "views/member_function_views.xml",

        "views/subscription_payment_wizard_views.xml",

        "views/member_account_views.xml",
        "views/member_account_transaction_views.xml",
        "views/association_payment_surplus_wizard_views.xml",
        "views/meeting_collection_surplus_wizard_views.xml",
        "views/member_wallet_transaction_views.xml",
        "views/subscription_cycle_close_wizard_views.xml",

        # Configuration (chargée avant les menus qui la référencent)
        "views/configuration_views.xml",

        # =====================================================
        # MENUS
        # =====================================================

        "views/menu_views.xml",

    ],


    "assets": {
        "web.assets_backend": [
            "primetech_association/static/src/dashboard/association_dashboard.js",
            "primetech_association/static/src/dashboard/association_dashboard.xml",
            "primetech_association/static/src/dashboard/association_dashboard.scss",

            "primetech_association/static/src/js/refresh_subscription_table.js",
        ],
    },

    "demo": [],

    "images": [
        "static/description/banner.png",
        "static/description/icon.png",
    ],

    "installable": True,

    "application": True,

    "auto_install": False,
}
