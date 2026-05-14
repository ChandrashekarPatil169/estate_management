/** @odoo-module **/

console.log("✅ Progress Color Patch JS Loaded");

import { ProgressBarField } from "@web/views/fields/progress_bar/progress_bar_field";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { SelectionField } from "@web/views/fields/selection/selection_field";
import { useState } from "@odoo/owl";


patch(ProgressBarField.prototype, {

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.progressColorConfig = [];

        onWillStart(async () => {
            // 🔥 ALWAYS fetch fresh config
            this.progressColorConfig = await this.orm.searchRead(
                "progress.config.line",
                [],
                ["min_value", "max_value", "color"]
            );
        });
    },

    get progressBarColorClass() {

        const value =
            this.props.record?.data?.[this.props.name] ?? 0;

        for (const line of this.progressColorConfig) {
            if (value >= line.min_value && value <= line.max_value) {
                return line.color || "bg-secondary";
            }
        }

        return "bg-secondary";
    },

});

class ColorOnlyField extends SelectionField {
    setup() {
        super.setup();
        this.state = useState({
            expanded: false,
        });
    }

    toggle() {
        this.state.expanded = !this.state.expanded;
    }

    select(value) {
        this.props.update(value);
        this.state.expanded = false;
    }
}

ColorOnlyField.template = "project_main_mgmt.ColorOnlyField";

registry.category("fields").add("color_only", {
    component: ColorOnlyField,
});

//console.log("✅ Progress Color Patch JS Loaded");
//working
///** @odoo-module **/
//
//import { ProgressBarField } from "@web/views/fields/progress_bar/progress_bar_field";
//import { patch } from "@web/core/utils/patch";
//import { useService } from "@web/core/utils/hooks";
//import { onWillStart } from "@odoo/owl";
//
//let progressColorConfig = [];
//
//patch(ProgressBarField.prototype, {
//
//    setup() {
//        super.setup();
//        this.orm = useService("orm");
//
//        onWillStart(async () => {
//            if (!progressColorConfig.length) {
//                progressColorConfig = await this.orm.searchRead(
//                    "progress.config.line",
//                    [],
//                    ["min_value", "max_value", "color"]
//                );
//            }
//        });
//    },
//
//    get progressBarColorClass() {
//
//        const value =
//            this.props.record?.data?.[this.props.name] ?? 0;
//
//        for (const line of progressColorConfig) {
//            if (value >= line.min_value && value <= line.max_value) {
//                return line.color;
//            }
//        }
//
//        return "bg-secondary";
//    },
//
//});

//import { ProgressBarField } from "@web/views/fields/progress_bar/progress_bar_field";
//import { patch } from "@web/core/utils/patch";
//
//patch(ProgressBarField.prototype, {
//
//    get progressBarColorClass() {
//
//        const value =
//            this.props.record?.data?.[this.props.name] ?? 0;
//
//        if (value <= 40) {
//            return "bg-danger o_force_color";
//        } else if (value <= 70) {
//            return "bg-warning o_force_color";
//        } else if (value <= 90) {
//            return "bg-success o_force_color";
//        } else {
//            return "bg-primary o_force_color";
//        }
//    },
//working
//});

///** @odoo-module **/
//
//function applyProgressColors() {
//
//    const bars = document.querySelectorAll(".o_progressbar_complete");
//    if (!bars.length) return;
//
//    fetch("/web/dataset/call_kw/progress.config.line/search_read", {
//        method: "POST",
//        headers: { "Content-Type": "application/json" },
//        body: JSON.stringify({
//            jsonrpc: "2.0",
//            method: "call",
//            params: {
//                model: "progress.config.line",
//                method: "search_read",
//                args: [[], ["min_value","max_value","color_code"]],
//                kwargs: {},
//            },
//            id: new Date().getTime(),
//        }),
//    })
//    .then(res => res.json())
//    .then(data => {
//
//        const lines = data.result || [];
//
//        bars.forEach(bar => {
//
//            const parent = bar.closest(".o_progressbar");
//            if (!parent) return;
//
//            const text = parent.innerText || "";
//            const match = text.match(/(\d+)\s*%/);
//            if (!match) return;
//
//            const value = parseInt(match[1]);
//
//            let colorClass = "";
//
//            lines.forEach(l => {
//                if (value >= l.min_value && value <= l.max_value){
//                    colorClass = l.color_code;   // 🔥 use color_code
//                }
//            });
//
//            if (colorClass){
//                bar.classList.remove(
//                    "bg-success","bg-danger","bg-warning",
//                    "bg-info","bg-primary","bg-dark"
//                );
//                bar.classList.add(colorClass);
//            }
//
//        });
//
//    });
//}
//
///* run after load */
//setTimeout(() => applyProgressColors(), 1200);
//
///* run when click */
//document.addEventListener("click", () => {
//    setTimeout(() => applyProgressColors(), 800);
//});