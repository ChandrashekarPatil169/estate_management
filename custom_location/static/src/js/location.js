/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class FetchLocationWidget extends Component {
    static template = "custom_location.FetchLocationBtn";

    setup() {
        this.notification = useService("notification");
    }

    async onClick() {
        const record = this.props.record;
        const resId = record.resId;

        console.log("Current Record ID:", resId);

        if (!resId) {
            this.notification.add("Save record first", { type: "warning" });
            return;
        }

        if (!navigator.geolocation) {
            this.notification.add("Geolocation not supported", { type: "warning" });
            return;
        }

        navigator.geolocation.getCurrentPosition(async (pos) => {
            try {
                const latitude = pos.coords.latitude.toFixed(6);
                const longitude = pos.coords.longitude.toFixed(6);

                console.log("Latitude:", latitude);
                console.log("Longitude:", longitude);

                const active_id = record.resId;
                const model = record.resModel;

                console.log("MODEL:", model);
                console.log("RES ID:", active_id);

                const locationData = await rpc(
                    "/custom/location/fetch_location_data",
                    { latitude, longitude }
                );

                if (locationData.error) {
                    this.notification.add("Failed to fetch address", { type: "danger" });
                    return;
                }

                const addr = locationData.address || {};

                const result = await rpc(
                    "/custom/location/update_location",
                    {
                        latitude,
                        longitude,
                        address: addr,
                        city: addr.city,
                        state: addr.state,
                        country: addr.country,
                        pincode: addr.pincode,
                        active_id: active_id,
                        model: model,
                    }
                );

                console.log("update_location response:", result);

                if (result.success) {
                    this.notification.add("Location updated", { type: "success" });

                    // Reload form properly
//                    await record.model.root.load();
                     await this.env.services.action.doAction({
                        type: "ir.actions.act_window",
                        res_model: record.resModel,
                        res_id: record.resId,
                        views: [[false, "form"]],
                        target: "current",
                     });
                } else {
                    this.notification.add("Update failed", { type: "danger" });
                }

            } catch (e) {
                console.error("RPC Exception:", e);
                this.notification.add("RPC error", { type: "danger" });
            }
        });
    }
}

registry.category("view_widgets").add("fetch_location", {
    component: FetchLocationWidget,
});