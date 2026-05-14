import { Component, useState, onMounted, onWillUnmount, onWillUpdateProps } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class TaskTimerWidget extends Component {
    static template = "rt_project_task_timer.TaskTimerWidget";
    static supportedTypes = ["char"];

    setup() {
        this.state = useState({ time: "00:00:00" });

        this.interval = null;

        onMounted(() => {
            this.syncWithRecord(this.props.record.data);
        });

        onWillUpdateProps((nextProps) => {
            this.syncWithRecord(nextProps.record.data);
        });

        onWillUnmount(() => {
            this.stopInterval();
        });
    }

    syncWithRecord(record) {
        this.stopInterval();

        const baseSeconds = record.task_accumulated_time || 0;

        if (record.timer_running && record.task_start_date) {

            const start = new Date(record.task_start_date);
            const now = new Date();
            const elapsed = Math.floor((now - start) / 1000);

            this.startTimestamp = Date.now();
            this.baseSeconds = baseSeconds + elapsed;

            this.updateDisplay(this.baseSeconds);

            this.interval = setInterval(() => {
                this.baseSeconds += 1;
                this.updateDisplay(this.baseSeconds);
            }, 1000);

        } else {
            this.updateDisplay(baseSeconds);
        }
    }

    stopInterval() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }

    updateDisplay(totalSeconds) {
        const h = Math.floor(totalSeconds / 3600);
        const m = Math.floor((totalSeconds % 3600) / 60);
        const s = totalSeconds % 60;

        this.state.time =
            String(h).padStart(2, "0") + ":" +
            String(m).padStart(2, "0") + ":" +
            String(s).padStart(2, "0");
    }
}

registry.category("fields").add("task_timer", {
    component: TaskTimerWidget,
});
//import { Component, useState, onMounted, onWillUnmount, onWillUpdateProps } from "@odoo/owl";
//import { registry } from "@web/core/registry";
//
//export class TaskTimerWidget extends Component {
//    static template = "rt_project_task_timer.TaskTimerWidget";
//    static supportedTypes = ["char"];
//
//    setup() {
//        this.state = useState({ time: "00:00:00" });
//
//        this.interval = null;
//        this.baseSeconds = 0;
//        this.startTimestamp = null;
//
//        onMounted(() => {
//            this.syncWithRecord(this.props.record.data);
//        });
//
//        onWillUpdateProps((nextProps) => {
//            this.syncWithRecord(nextProps.record.data);
//        });
//
//        onWillUnmount(() => {
//            this.stopInterval();
//        });
//    }
//
//    syncWithRecord(record) {
//        this.stopInterval();
//
//        this.baseSeconds = record.task_accumulated_time || 0;
//        this.updateDisplay(this.baseSeconds);
//
//        if (record.timer_running) {
//            this.startTimestamp = Date.now();
//            this.startInterval();
//        }
//    }
//
//    startInterval() {
//        this.interval = setInterval(() => {
//            const elapsed = Math.floor((Date.now() - this.startTimestamp) / 1000);
//            const total = this.baseSeconds + elapsed;
//            this.updateDisplay(total);
//        }, 1000);
//    }
//
//    stopInterval() {
//        if (this.interval) {
//            clearInterval(this.interval);
//            this.interval = null;
//        }
//    }
//
//    updateDisplay(totalSeconds) {
//        const h = Math.floor(totalSeconds / 3600);
//        const m = Math.floor((totalSeconds % 3600) / 60);
//        const s = totalSeconds % 60;
//
//        this.state.time =
//            String(h).padStart(2, "0") + ":" +
//            String(m).padStart(2, "0") + ":" +
//            String(s).padStart(2, "0");
//    }
//}
//
//registry.category("fields").add("task_timer", {
//    component: TaskTimerWidget,
//});

///** @odoo-module **/
//
//import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
//import { registry } from "@web/core/registry";
//import { useService } from "@web/core/utils/hooks";
//
//export class TaskTimerWidget extends Component {
//    static template = "rt_project_task_timer.TaskTimerWidget";
//    static supportedTypes = ["char"];
//
//    setup() {
//        this.orm = useService("orm");
//
//        this.timerState = useState({
//            displayTime: "00:00:00",
//            colorClass: "success"  // success (verde), warning (amarillo), danger (rojo)
//        });
//
//        this.intervalId = null;
//        this.accumulatedSeconds = 0;
//        this.isConcluded = false;
//        this.timerRunning = false;
//
//        // Valores configurables de tiempo (en horas)
//        this.yellowHours = 1.0;
//        this.redHours = 2.0;
//
//        onMounted(async () => {
//            // Cargar la configuración de tiempos
//            await this.loadTimerConfig();
//
//            // Cargar el tiempo acumulado y el estado
//            await this.loadTaskData();
//
//            // Iniciar actualización periódica si el temporizador está corriendo
//            if (this.timerRunning && !this.isConcluded) {
//                this.startPeriodicUpdate();
//            } else {
//                // Si está detenido, solo mostrar el tiempo acumulado
//                this.timerState.displayTime = this.formatTime(this.accumulatedSeconds);
//                this.updateColorClass();
//            }
//        });
//
//        onWillUnmount(() => {
//            // Limpiar el intervalo
//            this.stopPeriodicUpdate();
//        });
//    }
//
//    async loadTimerConfig() {
//        try {
//            // Obtener los parámetros de configuración
//            const params = await this.orm.call(
//                "ir.config_parameter",
//                "get_param",
//                ["rt_project_task_timer.yellow_hours", "1.0"]
//            );
//            this.yellowHours = parseFloat(params) || 1.0;
//
//            const redParams = await this.orm.call(
//                "ir.config_parameter",
//                "get_param",
//                ["rt_project_task_timer.red_hours", "2.0"]
//            );
//            this.redHours = parseFloat(redParams) || 2.0;
//        } catch (error) {
//            console.error("Error loading timer config:", error);
//            // Usar valores por defecto si hay error
//            this.yellowHours = 1.0;
//            this.redHours = 2.0;
//        }
//    }
//
//    async loadTaskData() {
//        try {
//            const recordId = this.props.record.resId;
//            if (recordId) {
//                const result = await this.orm.read(
//                    "project.task",
//                    [recordId],
//                    ["task_accumulated_time_realtime", "is_concluded", "timer_running"]
//                );
//                if (result && result.length > 0) {
//                    this.accumulatedSeconds = result[0].task_accumulated_time_realtime || 0;
//                    this.isConcluded = result[0].is_concluded || false;
//                    this.timerRunning = result[0].timer_running || false;
//                    this.timerState.displayTime = this.formatTime(this.accumulatedSeconds);
//                    this.updateColorClass();
//                }
//            }
//        } catch (error) {
//            console.error("Error loading task data:", error);
//        }
//    }
//
//    startPeriodicUpdate() {
//        if (this.intervalId) {
//            return; // Ya está corriendo
//        }
//
//        // Actualizar cada segundo refrescando desde el backend
//        this.intervalId = setInterval(async () => {
//            await this.loadTaskData();
//
//            // If timer stopped, stop polling
//            if (!this.timerRunning) {
//                this.stopPeriodicUpdate();
//            }
//        }, 1000);
////        this.intervalId = setInterval(async () => {
////            await this.loadTaskData();
////        }, 1000);
//    }
//
//    stopPeriodicUpdate() {
//        if (this.intervalId) {
//            clearInterval(this.intervalId);
//            this.intervalId = null;
//        }
//    }
//
//    updateColorClass() {
//        const hours = this.accumulatedSeconds / 3600.0;
//
//        if (hours >= this.redHours) {
//            this.timerState.colorClass = "danger";  // Rojo
//        } else if (hours >= this.yellowHours) {
//            this.timerState.colorClass = "warning";  // Amarillo
//        } else {
//            this.timerState.colorClass = "success";  // Verde
//        }
//    }
//
//    formatTime(totalSeconds) {
//        const hours = Math.floor(totalSeconds / 3600);
//        const minutes = Math.floor((totalSeconds % 3600) / 60);
//        const seconds = totalSeconds % 60;
//
//        return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
//    }
//}
//
//registry.category("fields").add("task_timer", {
//    component: TaskTimerWidget,
//});
