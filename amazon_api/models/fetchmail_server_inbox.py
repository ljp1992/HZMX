# -*- coding: utf-8 -*-
from odoo import tools, models, fields, api

class FetchmailServerInbox(models.Model):
    _inherit = 'fetchmail.server.inbox'

    shop_id = fields.Many2one('amazon.shop', string=u'店铺')

