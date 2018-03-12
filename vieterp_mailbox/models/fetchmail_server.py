# -*- coding: utf-8 -*-
from imaplib import IMAP4, IMAP4_SSL
from poplib import POP3, POP3_SSL
from odoo import tools, models, fields, api
MAIL_TIMEOUT = 60

class vieterp_fetchmail_server(models.Model):
    _inherit = 'fetchmail.server'
    _name = 'fetchmail.server.inbox'

    @api.model
    def _def_object_id(self):
        model_obj = self.env['ir.model']
        model = model_obj.search([('model', '=', 'mail.inbox')], limit = 1)
        if model:
            return model[0].id
        return False

    source_id = fields.Many2one('mail.server.source', string=u'邮件来源')
    object_id = fields.Many2one('ir.model', string=u"创建新的记录", default=_def_object_id)

    @api.multi
    def fetch_mail(self):
        result = super(vieterp_fetchmail_server, self).fetch_mail()
        return True

    @api.multi
    def connect(self):
        if self.source_id and self.source_id.id:
            self.ensure_one()
            if self.source_id.type == 'imap':
                if self.source_id.is_ssl:
                    connection = IMAP4_SSL(self.source_id.server, int(self.source_id.port))
                else:
                    connection = IMAP4(self.source_id.server, int(self.source_id.port))
                connection.login(self.user, self.password)
            elif self.type == 'pop':
                if self.source_id.is_ssl:
                    connection = POP3_SSL(self.source_id.server, int(self.source_id.port))
                else:
                    connection = POP3(self.source_id.server, int(self.source_id.port))
                # TODO: use this to remove only unread messages
                # connection.user("recent:"+server.user)
                connection.user(self.user)
                connection.pass_(self.password)
            # Add timeout on socket
            connection.sock.settimeout(MAIL_TIMEOUT)
            return connection
        return super(vieterp_fetchmail_server, self).connect()