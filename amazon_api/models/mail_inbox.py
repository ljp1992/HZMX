# -*- coding: utf-8 -*-
from odoo import tools, models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _

class MailInbox(models.Model):
    _inherit = 'mail.inbox'

    shop_id = fields.Many2one('amazon.shop', string=u'店铺')

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        context = self.env.context or {}
        shop_id = context.get('shop_id')
        if not shop_id:
            raise UserError('Not found amazon shop!')
        self = self.with_context(default_user_id=False)
        mail_data = {
            'subject': msg_dict.get('subject') or _(u"无主题"),
            'email_from': msg_dict.get('from'),
            'email_to': msg_dict.get('to'),
            'email_cc': msg_dict.get('cc'),
            'partner_id': msg_dict.get('author_id', False),
            'body_html': msg_dict.get('body', ''),
            'attachment_ids': msg_dict.get('attachments', []),
            'state': 'inbox',
            'shop_id': shop_id,
        }
        result = self.create(mail_data)
        return result


