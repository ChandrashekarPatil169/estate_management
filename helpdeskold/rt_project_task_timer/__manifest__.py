{
    'name': 'Widget Clock Project Task Timer',
    'version': '19.0.1.0.0',
    'category': 'Project',
    'summary': 'Automatic project task timer with time alerts and visual indicators',
    'description': """
        Project Task Timer - Automatic Time Tracking
        ============================================

        Automatically track time spent on project tasks with visual alerts
        and color-coded indicators based on elapsed time.

        Key Features:
        - Automatic timer starts when a task is created
        - Automatically stops when the task is moved to a completed stage
        - Real-time timer display in Form and Kanban views
        - Color-coded alerts:
          * Green: less than 1 hour
          * Yellow: between 1 and 2 hours
          * Red: more than 2 hours
        - Configurable time thresholds
        - UTC-based time tracking for consistent user experience
        - Task order field for better organization
        - Start and end date tracking
        - Accumulated time stored in seconds

        Functionality:
        ==============

        **Automatic Timer Start**
        The timer automatically starts when a new task is created.
        No manual action is required.

        **Smart Automatic Stop**
        The timer automatically stops when the task is moved to a
        completed stage (folded stages).

        **Kanban View Display**
        Displays the real-time timer in Kanban view in
        HH:MM:SS format with color-coded badges (green/yellow/red).

        **Customizable Configuration**
        Adjust the yellow and red alert time thresholds from:
        Settings → Project → Task Timer Configuration.

        **Time Zone Consistency**
        All time values are stored in UTC, ensuring consistent
        accumulated time display for all users regardless of timezone.

        **Timer States**
        - ⏱️ Running: Green/Yellow/Red badge depending on elapsed time
        - ⏸️ Paused: Gray badge with pause icon
        - ✓ Completed: Gray badge with check icon

        Installation:
        =============
        1. Download the module from Odoo Apps
        2. Install via Apps → Install Module
        3. Configure time thresholds (optional)

        Configuration:
        ==============
        Navigate to Settings → Project → Task Timer Configuration:
        - Yellow Alert Hours: Warning threshold (default: 1 hour)
        - Red Alert Hours: Critical threshold (default: 2 hours)

        Support:
        ========
        For technical support, contact: support@rootrivial.com
        Website: https://rootrivial.com
    """,
    'author': 'Rootrivial',
    'website': 'https://rootrivial.com',
    'depends': ['project'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_task_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'rt_project_task_timer/static/src/js/task_timer_widget.js',
            'rt_project_task_timer/static/src/xml/task_timer_widget.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'images': [
        "images/banner.png"
    ],
    'price': 0.00,
    'currency': 'USD',
}
# {
#     'name': 'Widget Clock Project Task Timer',
#     'version': '19.0.1.0.0',
#     'category': 'Project',
#     'summary': 'Temporizador automático para tareas de proyecto con alertas de tiempo e indicadores visuales',
#     'description': """
#         Temporizador de Tareas de Proyecto - Seguimiento Automático de Tiempo
#         ======================================================================
#
#         Rastrea automáticamente el tiempo dedicado a las tareas de proyecto con alertas
#         visuales e indicadores codificados por colores según el tiempo transcurrido.
#
#         Características Principales:
#         - Temporizador automático que inicia al crear una tarea
#         - Se detiene automáticamente cuando la tarea se mueve a una etapa de conclusión
#         - Visualización del temporizador en tiempo real en vistas de formulario y kanban
#         - Alertas codificadas por colores:
#           * Verde: menos de 1 hora
#           * Amarillo: entre 1 y 2 horas
#           * Rojo: más de 2 horas
#         - Umbrales de tiempo configurables
#         - Seguimiento de tiempo basado en UTC para experiencia consistente entre usuarios
#         - Campo de orden de tareas para organización
#         - Seguimiento de fechas de inicio y fin
#         - Tiempo acumulado en segundos
#
#         Funcionalidades:
#         ================
#
#         **Inicio Automático del Temporizador**
#         El temporizador se inicia automáticamente cuando creas una nueva tarea.
#         No se requiere intervención manual.
#
#         **Detención Inteligente Automática**
#         El temporizador se detiene automáticamente cuando mueves la tarea a una
#         etapa de conclusión (etapas plegadas).
#
#         **Visualización en Vista Kanban**
#         Muestra el temporizador en tiempo real en la vista kanban con formato
#         HH:MM:SS y badges codificados por colores (verde/amarillo/rojo).
#
#         **Configuración Personalizable**
#         Ajusta los umbrales de tiempo para las alertas amarilla y roja desde
#         Configuración → Proyecto → Configuración del Temporizador de Tareas.
#
#         **Seguimiento Consistente entre Zonas Horarias**
#         Todos los tiempos se almacenan en UTC, asegurando que todos los usuarios
#         vean el mismo tiempo acumulado sin importar su zona horaria.
#
#         **Estados del Temporizador**
#         - ⏱️ En Ejecución: Badge verde/amarillo/rojo según tiempo transcurrido
#         - ⏸️ Pausado: Badge gris con icono de pausa
#         - ✓ Concluido: Badge gris con icono de verificación
#
#         Instalación:
#         ============
#         1. Descarga el módulo desde Odoo Apps
#         2. Instala a través de Aplicaciones → Cargar Módulo
#         3. Configura los umbrales de tiempo (opcional)
#
#         Configuración:
#         ==============
#         Navega a Configuración → Proyecto → Configuración del Temporizador:
#         - Horas para Alerta Amarilla: Umbral de advertencia (predeterminado: 1 hora)
#         - Horas para Alerta Roja: Umbral de alerta (predeterminado: 2 horas)
#
#         Soporte:
#         ========
#         Para soporte técnico, contacta: support@rootrivial.com
#         Sitio web: https://rootrivial.com
#     """,
#     'author': 'Rootrivial',
#     'website': 'https://rootrivial.com',
#     'depends': ['project'],
#     'data': [
#         'security/ir.model.access.csv',
#         'views/project_task_views.xml',
#         'views/res_config_settings_views.xml',
#     ],
#     'assets': {
#         'web.assets_backend': [
#             'rt_project_task_timer/static/src/js/task_timer_widget.js',
#             'rt_project_task_timer/static/src/xml/task_timer_widget.xml',
#         ],
#     },
#     'installable': True,
#     'application': False,
#     'auto_install': False,
#     'license': 'LGPL-3',
#     'images': [
#                 "images/banner.png"
#               ],
#     'price': 0.00,
#     'currency': 'USD',
# }
