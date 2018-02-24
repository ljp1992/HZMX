# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ResUsers(models.Model):
    _inherit = 'res.users'

    shop_ids = fields.One2many('amazon.shop', 'operator_id', string=u'亚马逊店铺')

