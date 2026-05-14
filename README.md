# Estate Management

A large-scale collection of Odoo 19 modules for estate/property management, helpdesk operations, project management, procurement, and facility services.

## Modules

### Core Estate Modules

| Module | Version | Category | Description |
|--------|---------|----------|-------------|
| `estate_management` | 1.0 | Real Estate / Farm Management | Manage properties, buildings, floors, units, rooms, employees, and farms |
| `estate_dg_management` | 1.0 | Operations | Diesel generator management — fuel purchases, refills, and logs |
| `estate_coffee_management` | 1.0 | Miscellaneous | Coffee machine management — stock, refills, and cleaning |
| `custom_location` | 19.0.1 | Tools | Custom location management for HR and estate operations |

### Helpdesk Modules

| Module | Version | Category | Description |
|--------|---------|----------|-------------|
| `helpdesk_mgmt` | 19.0.0.0.0 | After-Sales | Full helpdesk ticket management system |
| `helpdesk_type` | 19.0.0.0.0 | After-Sales | Add ticket types to helpdesk |
| `helpdesk_type_sla` | 19.0.0.0.0 | HelpDesk Service | SLA management per ticket type |
| `helpdesk_mgmt_sla` | 19.0.0.0.0 | After-Sales | SLA tracking for helpdesk tickets |
| `helpdesk_ticket_email` | 1.0 | Helpdesk | Custom helpdesk flow with submit button and email notifications |
| `department_helpdesk` | 19.0.1.0.0 | Helpdesk | Adds department field to helpdesk tickets |
| `external_ticketing_dashboard` | 19.0.1.0.0 | Helpdesk | Dashboard for external ticketing with project and priority stats |
| `odoo_website_helpdesk_dashboard` | 19.0.1.0.0 | Website | Website helpdesk dashboard with charts and analytics |

### Project Modules

| Module | Version | Category | Description |
|--------|---------|----------|-------------|
| `project_category` | 1.0 | Project | Create categories for projects |
| `project_hierarchy_management` | 1.0 | Project | Parent/subproject hierarchy support |
| `project_main_mgmt` | 1.0 | Project | Smart buttons and advanced project management |
| `project_tabs` | 1.0 | Project | Manage different tabs in project views |
| `project_timeline` | 19.0.1.0.0 | Project Management | Timeline view for projects |
| `project_dashboard_odoo` | — | Project | Project dashboard with visual analytics |
| `expected_date` | 1.0 | Project | Expected date scheduling in projects |
| `rt_project_task_timer` | 19.0.1.0.0 | Project | Automatic task timer with time alerts and visual indicators |

### Procurement & Inventory Modules

| Module | Version | Category | Description |
|--------|---------|----------|-------------|
| `material_purchase_requisition` | 19.0.1.0.0 | Purchases | M0–M3 procurement with multi-level approvals |
| `purchase_rfq_approval` | 1.0 | Inventory / Purchase | Approval workflow for RFQs before PO confirmation |
| `custom_pr_qc` | 1.0 | Purchase | Material quality check with email notifications |
| `custom_inventory` | 1.0 | Inventory | Inventory management with asset tag and maintenance tracking |

### HR & Other Modules

| Module | Version | Category | Description |
|--------|---------|----------|-------------|
| `employee_travel_requisition` | 19.0.1.0.0 | Human Resources | Employee travel requisition management |
| `brute_force` | 19.0.1.0.0 | Tools | Authentication brute force protection with IP blocking |
| `GLPI` | 1.0 | Integration | GLPI IT asset management integration via cron |
| `ai_agent` | — | Tools | AI agent integration module |
| `web_timeline` | 19.0.1.0.2 | Web | Interactive timeline visualization chart |
| `web_widget_mermaid_field` | 0.0.4 | Technical | Mermaid.js diagram widget for Odoo views |

## Architecture

The modules follow a layered dependency structure:

```
estate_management (core)
├── estate_dg_management
├── estate_coffee_management
├── custom_inventory
└── custom_location

helpdesk_mgmt (core)
├── helpdesk_type
│   └── helpdesk_type_sla
├── helpdesk_mgmt_sla
├── helpdesk_ticket_email
├── department_helpdesk
└── external_ticketing_dashboard

project (Odoo core)
├── project_category
├── project_hierarchy_management
├── project_main_mgmt
├── project_tabs
├── project_timeline
└── expected_date
```

## Installation

1. Copy all modules into your Odoo addons directory.
2. Install core modules first:
   - `custom_location` → `estate_management` → other estate modules
   - `helpdesk_mgmt` → `helpdesk_type` → SLA and ticket modules
   - Project modules can be installed independently
3. Update the module list: **Settings → Technical → Update Apps List**.
4. Search for the desired module and click **Install**.

## Requirements

- Odoo 19.0 (Community or Enterprise)
- Python 3.10+
- Mermaid.js (bundled with `web_widget_mermaid_field`)

## License

Mixed — LGPL-3 and AGPL-3. See individual module manifests for details.
