/** @odoo-module **/

import { registry } from "@web/core/registry";

const actionRegistry = registry.category("actions");


async function refreshSubscriptionTable(env, action) {

    const params = action.params || {};

    const subscriptionId =
        params.subscription_id;

    const actionService =
        env.services.action;


    // =========================================================
    // FERMER LE WIZARD
    // =========================================================

    await actionService.doAction({
        type: "ir.actions.act_window_close",
    });


    // =========================================================
    // ATTENDRE LE RETOUR AU FORMULAIRE
    // =========================================================

    await new Promise(
        (resolve) => setTimeout(resolve, 150)
    );


    // =========================================================
    // CONTRÔLEUR PARENT
    // =========================================================

    const controller =
        actionService.currentController;

    if (
        !controller
        || !controller.model
        || !controller.model.root
    ) {
        return;
    }


    const model =
        controller.model;

    const root =
        model.root;


    // =========================================================
    // FORMULAIRE COTISATION
    // =========================================================

    if (
        root.resModel
        !== "association.subscription"
    ) {
        return;
    }


    if (
        subscriptionId
        && root.resId
        && root.resId !== subscriptionId
    ) {
        return;
    }


    // =========================================================
    // RELECTURE ORM DU RECORD PARENT
    //
    // PAS DE RELOAD NAVIGATEUR
    // PAS DE RECHARGEMENT D'ACTION
    //
    // OWL RELIT LES VALEURS DU FORMULAIRE
    // ET MET À JOUR LE ONE2MANY
    // =========================================================

    await root.load();


    // =========================================================
    // NOTIFIER OWL
    // =========================================================

    model.notify();
}


actionRegistry.add(
    "primetech_refresh_subscription_table",
    refreshSubscriptionTable
);