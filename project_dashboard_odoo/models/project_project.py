# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: AYANA KP @cybrosys(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import random
from odoo import models,fields,api


class ProjectProject(models.Model):
    """This class inherits from 'project.project' and adds custom functionality
    to it.It provides methods to work with project data."""
    _inherit = 'project.project'

    last_update_status = fields.Selection(
        selection_add=[('new', 'New')],
        ondelete={
            'new': lambda records: records.write({'last_update_status': 'on_track'})
        }
    )

    def get_color_code(self):
        """Generate a random color code in hexadecimal format.
        :return: A random color code in the format '#RRGGBB.'"""
        color = f"#{random.randint(0, 0xFFFFFF):06x}"
        return color



class ProjectUpdate(models.Model):
    _inherit = 'project.update'

    status = fields.Selection(
    selection_add=[('new', 'New')],
    ondelete={
        'new': lambda records: records.write({'status': 'on_track'})
            }
    )

    @api.depends('status')
    def _compute_color(self):
        custom_status_color = {
            'new': 0, # choose suitable color index
            'review': 3,
            'cancelled': 1,
            }

        for update in self:
            if update.status in custom_status_color:
                update.color = custom_status_color[update.status]
            else:
                # fallback to base mapping manually
                base_status_color = {
                'on_track': 10,
                'at_risk': 2,
                'off_track': 1,
                'on_hold': 4,
                'done': 7,
                }
                update.color = base_status_color.get(update.status, 0)