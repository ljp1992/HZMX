# -*- coding: utf-8 -*-
from odoo import tools, models, fields, api
from odoo.exceptions import UserError

class MailInbox(models.Model):
    _inherit = 'mail.inbox'

    shop_id = fields.Many2one('amazon.shop', string=u'店铺')
