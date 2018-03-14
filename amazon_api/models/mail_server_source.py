# -*- coding: utf-8 -*-
from odoo import tools, models, fields, api

class mail_server_source(models.Model):
    _inherit = 'mail.server.source'

    smtp_host = fields.Char(required=True, string=u'SMTP服务器')

    smtp_port = fields.Integer(required=True, string=u'SMTP端口')

    smtp_encryption = fields.Selection([
        ('none', u'不加密'),
        ('starttls', u'TLS(STARTTLS)'),
        ('ssl', u'SSL/TLS'),
    ], default='none', required=True, string=u'连接安全')

    @api.onchange('smtp_encryption')
    def onchange_smtp_encryption(self):
        if self.smtp_encryption in ['none', 'starttls']:
            self.smtp_port = 25
        elif self.smtp_encryption == 'ssl':
            self.smtp_port = 465
