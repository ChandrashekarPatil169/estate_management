import requests
from odoo import models, fields, api
from odoo.exceptions import UserError

class GLPIIntegration(models.Model):
    _inherit = 'custom.inventory'

    glpi_id = fields.Integer(index=True)
    last_sync_date = fields.Datetime()
    ram_info = fields.Char(string="RAM Info")
    storage_info = fields.Char(string="Storage Info")

    def _glpi_session(self):
        url = self.env['ir.config_parameter'].sudo().get_param('glpi.base.url') + '/initSession'
        headers = {
            'App-Token': self.env['ir.config_parameter'].sudo().get_param('glpi.app.token'),
            'Authorization': 'user_token ' + self.env['ir.config_parameter'].sudo().get_param('glpi.user.token')
        }
        res = requests.get(url, headers=headers,verify=False)
        # return res.json().get('session_token')
        if res.status_code != 200:
            raise UserError(f"GLPI Session Error: {res.text}")

        return res.json().get('session_token')

    def action_sync_glpi(self):
        session = self._glpi_session()
        base = self.env['ir.config_parameter'].sudo().get_param('glpi.base.url')

        headers = {
            'Session-Token': session,
            'App-Token': self.env['ir.config_parameter'].sudo().get_param('glpi.app.token')
        }

        computers = requests.get(base + '/Computer', headers=headers, verify=False).json()
        for comp in computers:
            print("GLPI COMPUTER:", comp)
            serial = comp.get('serial')
            record = self.search([('serial_no', '=', serial)], limit=1)

            ram = requests.get(base + f"/Computer_DeviceMemory?criteria[0][field]=computers_id&criteria[0][searchtype]=equals&criteria[0][value]={comp['id']}",headers=headers,verify=False).json()
            disk = requests.get(base + f"/Computer_DeviceHardDrive?criteria[0][field]=computers_id&criteria[0][searchtype]=equals&criteria[0][value]={comp['id']}", headers=headers,verify=False).json()

            ram_str = str(ram)
            disk_str = str(disk)

            if record:
                changes = []
                if record.ram_info != ram_str:
                    changes.append(f"RAM Changed: {record.ram_info} → {ram_str}")
                    record.ram_info = ram_str
                if record.storage_info != disk_str:
                    changes.append(f"Storage Changed: {record.storage_info} → {disk_str}")
                    record.storage_info = disk_str

                if changes:
                    record.message_post(
                        body="<br/>".join(changes),
                        subject="GLPI Hardware Update"
                    )
