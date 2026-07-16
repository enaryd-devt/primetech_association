/** @odoo-module **/

import {
    Component,
    onWillStart,
    useState,
} from "@odoo/owl";

import {
    registry,
} from "@web/core/registry";

import {
    useService,
} from "@web/core/utils/hooks";


export class AssociationDashboard extends Component {

    static template =
        "primetech_association.AssociationDashboard";

    setup() {

        this.orm = useService("orm");

        this.action = useService("action");

        this.state = useState({

            loading: true,

            data: {
                company: {},
                members: {},
                meetings: {},
                subscriptions: {},
                payments: {},
                treasury: {},
                penalties: {},
                recent_payments: [],
                next_meeting: false,
                currency: {},
            },

        });

        onWillStart(
            async () => {

                await this.loadDashboard();

            }
        );

    }


    // =========================================================
    // CHARGEMENT
    // =========================================================

    async loadDashboard() {

        this.state.loading = true;

        try {

            const data = await this.orm.call(
                "association.dashboard",
                "get_dashboard_data",
                [],
            );

            this.state.data = data;

        } finally {

            this.state.loading = false;

        }

    }


    // =========================================================
    // FORMAT MONTANT
    // =========================================================

    formatAmount(amount) {

        const value = Number(
            amount || 0
        );

        return new Intl.NumberFormat(
            "fr-FR",
            {
                maximumFractionDigits: 0,
            }
        ).format(value);

    }


    // =========================================================
    // NAVIGATION
    // =========================================================

    async openAction(xmlId) {

        await this.action.doAction(xmlId);

    }


    openMembers() {

        return this.openAction(
            "primetech_association.action_association_member"
        );

    }


    openMeetings() {

        return this.openAction(
            "primetech_association.action_meeting"
        );

    }


    openSubscriptions() {

        return this.openAction(
            "primetech_association.action_subscription"
        );

    }


    openPayments() {

        return this.openAction(
            "primetech_association.action_payment"
        );

    }


    openTreasury() {

        return this.openAction(
            "primetech_association.action_association_fund"
        );

    }


    openPenalties() {

        return this.openAction(
            "primetech_association.action_penalty"
        );

    }


    openMeeting(meetingId) {

        if (!meetingId) {
            return;
        }

        return this.action.doAction({
            type: "ir.actions.act_window",
            name: "Réunion",
            res_model: "association.meeting",
            res_id: meetingId,
            views: [
                [
                    false,
                    "form",
                ],
            ],
            target: "current",
        });

    }

}


registry
    .category("actions")
    .add(
        "primetech_association.dashboard",
        AssociationDashboard
    );