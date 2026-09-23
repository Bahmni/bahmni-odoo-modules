import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

registry.category("ir.actions.report handlers").add("xlsx", async (action, options, env) => {
    if (action.report_type === 'stock_xlsx') {
        env.services.ui.block();
        try {
            await download({
                url: '/xlsx_report',
                data: action.data,
            });
        } catch (error) {
            if (env.services.notification) {
                env.services.notification.add(
                    error.message || "An error occurred while generating the Excel report.",
                    { type: "danger" }
                );
            }
        } finally {
            env.services.ui.unblock();
        }
        return true;
    }
});