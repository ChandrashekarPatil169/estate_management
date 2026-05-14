{
    'name': 'Custom Inventory',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Inventory Management with Asset Tag and Maintenance Tracking',
    'depends': ['base', 'hr', 'mail', 'estate_management', 'website','project','web'],
    'data': [
        'security/security.xml',
        'security/record_rules.xml',

        'security/ir.model.access.csv',
         'data/cron.xml',
        'views/inventory_views.xml',
        'views/miscllanious.xml',
        # 'views/inventory_views.xml',
        'views/inventory_movement_views.xml',
        'views/software_views.xml',
        'views/inventory_model_master_views.xml',
        'data/ticket_sequence.xml',
        'views/ticket_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

#
# | Role      | Own | Same Warehouse | Others | Follower | All Records |
# | --------- | --- | -------------- | ------ | -------- | ----------- |
# | Executive | ✅   | ❌              | ❌      | ✅        | ❌           |
# | Manager   | ✅   | ✅              | ❌      | ✅        | ❌           |
# | Admin     | ✅   | ✅              | ✅      | ✅        | ✅           |
#



#
# Perfect 👍 — let’s freeze your final system so you can safely move forward.
# I’ll give you complete final blueprint (no confusion, production-ready understanding).
#
# 🧠 🔥 FINAL DOMAIN LOGIC (YOUR SYSTEM)
# 👤 EXECUTIVE LOGIC
#
# 👉 Executive can see ONLY:
#
# [
#     '|',
#     ('create_uid', '=', user.id),
#     ('message_partner_ids', 'in', [user.partner_id.id])
# ]
# ✅ Meaning (real life)
# ✔ Own records
# ✔ Follower records
# ❌ Same warehouse records
# ❌ Manager/Admin records
# 👨‍💼 MANAGER LOGIC
#
# 👉 Manager can see:
#
# [
#     '|',
#     ('message_partner_ids', 'in', [user.partner_id.id]),
#     '|',
#         ('create_uid', '=', user.id),
#         ('warehouse_id', 'in', user.warehouse_manager_ids.ids)
# ]
# ✅ Meaning
# ✔ Own records
# ✔ Follower records
# ✔ All records in manager warehouses
# ❌ Outside warehouse
# 👑 ADMIN LOGIC
#
# 👉 No rules applied
#
# ✔ Sees everything
# ✔ Full CRUD
# 🔒 FOLLOWER LOGIC (GLOBAL)
#
# 👉 Applies to ALL users
#
# ('message_partner_ids', 'in', [user.partner_id.id])
# ✅ Meaning
# If user is follower → ALWAYS can see
# 🧠 FINAL ACCESS MODEL
# Role	Own	Warehouse	Follower	All
# Executive	✅	❌	✅	❌
# Manager	✅	✅	✅	❌
# Admin	✅	✅	✅	✅
# 🧩 🔥 FIELDS YOU ADDED
# In res.users
# warehouse_exec_ids = fields.Many2many(
#     'inventory.warehouse',
#     'res_users_exec_warehouse_rel',
#     'user_id',
#     'warehouse_id',
#     string="Executive Warehouses"
# )
#
# warehouse_manager_ids = fields.Many2many(
#     'inventory.warehouse',
#     'res_users_manager_warehouse_rel',
#     'user_id',
#     'warehouse_id',
#     string="Manager Warehouses"
# )
# In your model (custom.inventory)
#
# 👉 Already exists:
#
# warehouse_id = fields.Many2one('inventory.warehouse')
#
# 👉 Required for manager logic
#
# 📜 🔥 FINAL XML RULES
# <odoo>
#     <data noupdate="0">
#
#         <!-- EXECUTIVE -->
#         <record id="rule_exec_custom_inventory" model="ir.rule">
#             <field name="name">Executive Access</field>
#             <field name="model_id" ref="model_custom_inventory"/>
#             <field name="groups" eval="[(4, ref('custom_inventory.group_warehouse_executive'))]"/>
#             <field name="domain_force">
#                 [
#                     '|',
#                     ('create_uid', '=', user.id),
#                     ('message_partner_ids', 'in', [user.partner_id.id])
#                 ]
#             </field>
#         </record>
#
#         <!-- MANAGER -->
#         <record id="rule_manager_custom_inventory" model="ir.rule">
#             <field name="name">Manager Access</field>
#             <field name="model_id" ref="model_custom_inventory"/>
#             <field name="groups" eval="[(4, ref('custom_inventory.group_warehouse_manager'))]"/>
#             <field name="domain_force">
#                 [
#                     '|',
#                     ('message_partner_ids', 'in', [user.partner_id.id]),
#                     '|',
#                         ('create_uid', '=', user.id),
#                         ('warehouse_id', 'in', user.warehouse_manager_ids.ids)
#                 ]
#             </field>
#         </record>
#
#     </data>
# </odoo>
# 🔐 ACCESS CONTROL (CSV)
# access_custom_inventory_exec,access_custom_inventory_exec,model_custom_inventory,custom_inventory.group_warehouse_executive,1,1,1,1
# access_custom_inventory_manager,access_custom_inventory_manager,model_custom_inventory,custom_inventory.group_warehouse_manager,1,1,1,1
# access_custom_inventory_admin,custom.inventory.admin,model_custom_inventory,base.group_system,1,1,1,1
# 🧪 FINAL TEST LOGIC (MENTAL CHECK)
# Executive:
# sees own ✔
# sees follower ✔
# cannot see others ✔
# Manager:
# sees own ✔
# sees warehouse ✔
# sees follower ✔
# Mixed user:
# behaves per warehouse ✔
# 🚨 IMPORTANT RULES YOU FOLLOWED
#
# ✔ No ref() inside domain
# ✔ No dynamic Python inside domain
# ✔ No duplicate rules
# ✔ No create rule misuse
# ✔ Clean separation of roles
#
# 💥 FINAL SYSTEM TYPE
#
# 🔒 Role-based + Warehouse-based + Follower override system
#
# 🎯 FINAL ANSWER
#
# 👉 This is your final stable architecture
# 👉 You can safely move to next phase
