//perfect part 4
/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

console.log("🔥 GLOBAL ERROR HANDLER ACTIVE");

function cleanMessage(msg) {
    if (!msg) return "";

    // 🔥 REMOVE DATABASE NAME PATTERN
    // Example: "on localhost:8069 on model..."
    return msg
        .replace(/on\s+\S+:\d+/g, "")   // remove localhost:8069
        .replace(/on\s+model\s+\S+/g, "") // remove model info if needed
        .replace(/\s+/g, " ")           // normalize spaces
        .trim();
}

function customErrorHandler(env, error) {

    console.log("🧠 FULL ERROR:", error);

    const errorData =
        error?.data ||
        error?.error?.data ||
        error?.cause?.data ||
        {};

    const name = errorData.name || "";
    const message = errorData.message || "";

    // =====================================
    // ✅ VALIDATION → DEFAULT
    // =====================================
    if (name.includes("ValidationError") ||
        name.includes("UserError") ||
        name.includes("AccessError")) {
        return false;
    }

    // =====================================
    // 🔥 CLEAN MESSAGE
    // =====================================
    const cleanedMessage = cleanMessage(message);

    // =====================================
    // 🔥 CUSTOM POPUP
    // =====================================
//    env.services.dialog.add(AlertDialog, {
//        title: _t("System Error"),
//        body: cleanedMessage || _t("A technical error occurred."),
//        confirmLabel: _t("Close"),
//    });
     if (env?.services?.dialog) {
    env.services.dialog.add(AlertDialog, {
        title: _t("System Error"),
        body: cleanedMessage || _t("A technical error occurred."),
        confirmLabel: _t("Close"),
    });
} else {
    console.warn("⚠️ Dialog service not ready, skipping popup");
}

    return true;
}

// =====================================
registry.category("error_handlers").add(
    "hide_technical_details",
    customErrorHandler,
    { sequence: -100 }
);


























////part 3
//import { registry } from "@web/core/registry";
//import { _t } from "@web/core/l10n/translation";
//import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
//import { patch } from "@web/core/utils/patch";
//import { errorService } from "@web/core/errors/error_service";
//
//console.log("🔥 GLOBAL ERROR HANDLER ACTIVE");
//
//// ===============================
//// 1. RPC + VALIDATION HANDLER
//// ===============================
//function customErrorHandler(env, error) {
//
//    const errorData = error?.data || error?.error?.data || {};
//    const exceptionName = errorData.name || "";
//
//    const isBusinessError =
//        exceptionName.startsWith("odoo.exceptions.");
//
//    if (isBusinessError) {
//        return false; // default Odoo popup
//    }
//
//    env.services.dialog.add(AlertDialog, {
//        title: _t("System Error"),
//        body: _t(
//            "A technical error occurred while processing your request. Please contact support if it continues."
//        ),
//        confirmLabel: _t("Close"),
//    });
//
//    return true;
//}
//
//// ===============================
//// 2. GLOBAL ERROR PATCH (SAFE)
//// ===============================
//patch(errorService, {
//
//    handleError(original, error) {
//
//        console.error("🔥 GLOBAL ERROR CAUGHT:", error);
//
//        // 🔥 CUSTOM POPUP
//        this.env.services.dialog.add(AlertDialog, {
//            title: _t("System Error"),
//            body: _t(
//                "A technical system error occurred (installation / crash). Please contact support."
//            ),
//            confirmLabel: _t("Close"),
//        });
//
//        // ❌ DO NOT CALL ORIGINAL → blocks "Oops"
//        return;
//    }
//
//});
//
//// ===============================
//// REGISTER HANDLER
//// ===============================
//registry.category("error_handlers").add(
//    "hide_technical_details",
//    customErrorHandler,
//    { sequence: -100 }
//);




//====> part 2
///** @odoo-module **/
//
//import { registry } from "@web/core/registry";
//import { _t } from "@web/core/l10n/translation";
//import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
//
//console.log("🔥 GLOBAL ERROR HANDLER ACTIVE");
//
//function customErrorHandler(env, error) {
//
//    console.log("🧠 FULL ERROR OBJECT:", error);
//
//    const errorData = error?.data || error?.error?.data || {};
//    const exceptionName = errorData.name || "";
//
//    // ✅ LET ODOO HANDLE ALL BUSINESS ERRORS FIRST
//    if (exceptionName.startsWith("odoo.exceptions.")) {
//        console.log("✅ BUSINESS ERROR → LET ODOO HANDLE");
//        return false;
//    }
//
//    // 🔥 ONLY HANDLE UNCAUGHT TECHNICAL ERRORS
//    console.error("🚨 TECHNICAL ERROR CAUGHT:", error);
//
//    env.services.dialog.add(AlertDialog, {
//        title: _t("System Error"),
//        body: _t(
//            "An unexpected technical issue has occurred. Please contact the support team if the problem persists."
//        ),
//        confirmLabel: _t("Close"),
//    });
//
//    return true;
//}
//
//// ✅ RUN AFTER ODOO DEFAULT HANDLERS
//registry.category("error_handlers").add(
//    "hide_technical_details",
//    customErrorHandler,
//    { sequence: 100 }   // 🔥 THIS FIXES YOUR ISSUE
//);











//====> main one
///** @odoo-module **/
//
//import { registry } from "@web/core/registry";
//import { _t } from "@web/core/l10n/translation";
//import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
//
//console.log("🔥 GLOBAL ERROR HANDLER ACTIVE");
//
//function customErrorHandler(env, error) {
//
//    const errorData = error?.data || error?.error?.data || {};
//
//    const exceptionName =
//        errorData.name ||
//        errorData.exception_name ||
//        error?.exceptionName ||
//        error?.message ||
//        "";
//
//    // ✅ FLEXIBLE BUSINESS ERROR CHECK
//    const isBusinessError =
//        exceptionName.includes("ValidationError") ||
//        exceptionName.includes("UserError") ||
//        exceptionName.includes("AccessError") ||
//        exceptionName.includes("RedirectWarning") ||
//        error.type === "validation";
//
//    // ✅ LET ODOO HANDLE THESE
//    if (isBusinessError) {
//        return false;
//    }
//
//    // 🔥 HANDLE ALL OTHER ERRORS
//    console.error("Technical Error Hidden:", error);
//
//    env.services.dialog.add(AlertDialog, {
//        title: _t("System Error"),
//        body: _t(
//            "An unexpected technical issue has occurred. Please contact the support team if the problem persists."
//        ),
//        confirmLabel: _t("Close"),
//    });
//
//    return true;
//}
//
//// ✅ IMPORTANT: sequence must be LOW (higher priority)
//registry.category("error_handlers").add(
//    "hide_technical_details",
//    customErrorHandler,
//    { sequence: -100 }
//);
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
