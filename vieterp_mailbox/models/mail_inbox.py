# -*- coding: utf-8 -*-
from lxml import etree
from odoo import tools, models, fields, api, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.exceptions import UserError, AccessError

class vieterp_mail_inbox(models.Model):
    _inherit = ['mail.mail']
    _name = 'mail.inbox'

    fetchmail_server_id = fields.Many2one('fetchmail.server.inbox', u"收件服务器", readonly=True, index=True,
                                          oldname='server_id')
    template_id = fields.Many2one('mail.template', string=u'邮件模板', index=True)
    state = fields.Selection([
        ('inbox', u'收件箱'),
        ('outgoing', u'发送中'),
        ('sent', u'已发送'),
        ('received', u'已接收'),
        ('exception', u'发送失败'),
        ('cancel', u'已取消'),
    ], 'Status', readonly=True, copy=False, default='outgoing')
    trader_id = fields.Many2one('res.partner', u'商户',
                default=lambda self: self.env.user.partner_id.parent_id or self.env.user.partner_id)

    @api.model
    def message_new(self, msg_dict, custom_values=None):
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
        }
        result = self.create(mail_data)
        return result

    @api.multi
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, subtype=None, **kwargs):
        message_data = {
            'subject': kwargs.get('subject'),
            'date': kwargs.get('date'),
            'body': kwargs.get('body'),
            'email_from': kwargs.get('email_from'),
            'reply_to': kwargs.get('email_from'),
        }
        return self.env['mail.message'].create(message_data)

    # @api.model
    # def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
    #     context = self._context
    #     result = super(vieterp_mail_inbox, self).fields_view_get(view_id, view_type, toolbar, submenu)
    #     if view_type == 'form':
    #         current_id = context.get('active_id', False)
    #         my_state = self.browse(current_id).state
    #         if my_state in ['inbox', 'outgoing']:
    #             doc = etree.XML(result['arch'])
    #             for node in doc.xpath('//form'):
    #                 node.set('edit', 'true')
    #             result['arch'] = etree.tostring(doc)
    #     return result

    @api.onchange('template_id')  # if template are changed, call method
    def check_template_change(self):
        """ - mass_mailing: we cannot render, so return the template values
            - normal mode: return rendered values """
        if self.template_id and self.template_id.id:
            self.subject = self.template_id.subject
            self.body_html = self.template_id.body_html
            self.reply_to = self.template_id.reply_to
            self.mail_server_id = self.template_id.mail_server_id
            if self.template_id.attachment_ids:
                self.attachment_ids = [att.id for att in template.attachment_ids]
            if self.template_id.mail_server_id:
                self.mail_server_id = self.template_id.mail_server_id.id
            if self.template_id.user_signature and self.body_html:
                signature = self.env['res.users'].browse(self._uid).signature
                self.body = tools.append_content_to_html(self.body, signature, plaintext=False)
        else:
            if not self.body_html:
                signature = self.env['res.users'].browse(self._uid).signature
                self.body_html = signature


class b2b_mail_message(models.Model):
    _inherit = ['mail.message']
    _name = 'mail.message'

    trader_id = fields.Many2one('res.partner', u'商户',
                                default=lambda self: self.env.user.partner_id.parent_id or self.env.user.partner_id)

    @api.multi
    def check_access_rule(self, operation):
        """ Access rules of mail.message:
            - read: if
                - author_id == pid, uid is the author OR
                - uid is in the recipients (partner_ids) OR
                - uid is member of a listern channel (channel_ids.partner_ids) OR
                - uid have read access to the related document if model, res_id
                - otherwise: raise
            - create: if
                - no model, no res_id (private message) OR
                - pid in message_follower_ids if model, res_id OR
                - uid can read the parent OR
                - uid have write or create access on the related document if model, res_id, OR
                - otherwise: raise
            - write: if
                - author_id == pid, uid is the author, OR
                - uid is in the recipients (partner_ids) OR
                - uid has write or create access on the related document if model, res_id
                - otherwise: raise
            - unlink: if
                - uid has write or create access on the related document if model, res_id
                - otherwise: raise

        Specific case: non employee users see only messages with subtype (aka do
        not see internal logs).
        """

        def _generate_model_record_ids(msg_val, msg_ids):
            """ :param model_record_ids: {'model': {'res_id': (msg_id, msg_id)}, ... }
                :param message_values: {'msg_id': {'model': .., 'res_id': .., 'author_id': ..}}
            """
            model_record_ids = {}
            for id in msg_ids:
                vals = msg_val.get(id, {})
                if vals.get('model') and vals.get('res_id'):
                    model_record_ids.setdefault(vals['model'], set()).add(vals['res_id'])
            return model_record_ids

        # 下段内容为QDOO所添加，其余为ODOO原码
        ###################################################
        parnter = self.env.user.partner_id.parent_id or self.env.user.partner_id
        if len(self) > 0:
            self.sudo()._cr.execute("""SELECT message_type, trader_id FROM mail_message WHERE id = %s;""" % self[0].id)
            result = self._cr.fetchall()
            msg_type = result[0][0]
            trader = int(result[0][1])
            if parnter and msg_type == 'email' and trader == parnter.id:
                return
        ###################################################
        if self._uid == SUPERUSER_ID:
            return
        # Non employees see only messages with a subtype (aka, not internal logs)
        if not self.env['res.users'].has_group('base.group_user'):
            self._cr.execute('''SELECT DISTINCT message.id, message.subtype_id, subtype.internal
                                    FROM "%s" AS message
                                    LEFT JOIN "mail_message_subtype" as subtype
                                    ON message.subtype_id = subtype.id
                                    WHERE message.message_type = %%s AND (message.subtype_id IS NULL OR subtype.internal IS TRUE) AND message.id = ANY (%%s)''' % (
            self._table), ('comment', self.ids,))
            if self._cr.fetchall():
                raise AccessError(
                    _(
                        'The requested operation cannot be completed due to security restrictions. Please contact your system administrator.\n\n(Document type: %s, Operation: %s)') %
                    (self._description, operation))

        # Read mail_message.ids to have their values
        message_values = dict((res_id, {}) for res_id in self.ids)

        if operation in ['read', 'write']:
            self._cr.execute("""SELECT DISTINCT m.id, m.model, m.res_id, m.author_id, m.parent_id, partner_rel.res_partner_id, channel_partner.channel_id as channel_id
                    FROM "%s" m
                    LEFT JOIN "mail_message_res_partner_rel" partner_rel
                    ON partner_rel.mail_message_id = m.id AND partner_rel.res_partner_id = (%%s)
                    LEFT JOIN "mail_message_mail_channel_rel" channel_rel
                    ON channel_rel.mail_message_id = m.id
                    LEFT JOIN "mail_channel" channel
                    ON channel.id = channel_rel.mail_channel_id
                    LEFT JOIN "mail_channel_partner" channel_partner
                    ON channel_partner.channel_id = channel.id AND channel_partner.partner_id = (%%s)
                    WHERE m.id = ANY (%%s)""" % self._table,
                             (self.env.user.partner_id.id, self.env.user.partner_id.id, self.ids,))
            for mid, rmod, rid, author_id, parent_id, partner_id, channel_id in self._cr.fetchall():
                message_values[mid] = {
                    'model': rmod,
                    'res_id': rid,
                    'author_id': author_id,
                    'parent_id': parent_id,
                    'notified': any((message_values[mid].get('notified'), partner_id, channel_id))
                }
        else:
            self._cr.execute(
                """SELECT DISTINCT id, model, res_id, author_id, parent_id FROM "%s" WHERE id = ANY (%%s)""" % self._table,
                (self.ids,))
            for mid, rmod, rid, author_id, parent_id in self._cr.fetchall():
                message_values[mid] = {'model': rmod, 'res_id': rid, 'author_id': author_id, 'parent_id': parent_id}

        # Author condition (READ, WRITE, CREATE (private))
        author_ids = []
        if operation == 'read' or operation == 'write':
            author_ids = [mid for mid, message in message_values.iteritems()
                          if message.get('author_id') and message.get('author_id') == self.env.user.partner_id.id]
        elif operation == 'create':
            author_ids = [mid for mid, message in message_values.iteritems()
                          if not message.get('model') and not message.get('res_id')]

        # Parent condition, for create (check for received notifications for the created message parent)
        notified_ids = []
        if operation == 'create':
            # TDE: probably clean me
            parent_ids = [message.get('parent_id') for mid, message in message_values.iteritems()
                          if message.get('parent_id')]
            self._cr.execute("""SELECT DISTINCT m.id, partner_rel.res_partner_id, channel_partner.partner_id FROM "%s" m
                    LEFT JOIN "mail_message_res_partner_rel" partner_rel
                    ON partner_rel.mail_message_id = m.id AND partner_rel.res_partner_id = (%%s)
                    LEFT JOIN "mail_message_mail_channel_rel" channel_rel
                    ON channel_rel.mail_message_id = m.id
                    LEFT JOIN "mail_channel" channel
                    ON channel.id = channel_rel.mail_channel_id
                    LEFT JOIN "mail_channel_partner" channel_partner
                    ON channel_partner.channel_id = channel.id AND channel_partner.partner_id = (%%s)
                    WHERE m.id = ANY (%%s)""" % self._table,
                             (self.env.user.partner_id.id, self.env.user.partner_id.id, parent_ids,))
            not_parent_ids = [mid[0] for mid in self._cr.fetchall() if any([mid[1], mid[2]])]
            notified_ids += [mid for mid, message in message_values.iteritems()
                             if message.get('parent_id') in not_parent_ids]

        # Recipients condition, for read and write (partner_ids) and create (message_follower_ids)
        other_ids = set(self.ids).difference(set(author_ids), set(notified_ids))
        model_record_ids = _generate_model_record_ids(message_values, other_ids)
        if operation in ['read', 'write']:
            notified_ids = [mid for mid, message in message_values.iteritems() if message.get('notified')]
        elif operation == 'create':
            for doc_model, doc_ids in model_record_ids.items():
                followers = self.env['mail.followers'].sudo().search([
                    ('res_model', '=', doc_model),
                    ('res_id', 'in', list(doc_ids)),
                    ('partner_id', '=', self.env.user.partner_id.id),
                ])
                fol_mids = [follower.res_id for follower in followers]
                notified_ids += [mid for mid, message in message_values.iteritems()
                                 if message.get('model') == doc_model and message.get('res_id') in fol_mids]

        # CRUD: Access rights related to the document
        other_ids = other_ids.difference(set(notified_ids))
        model_record_ids = _generate_model_record_ids(message_values, other_ids)
        document_related_ids = []
        for model, doc_ids in model_record_ids.items():
            DocumentModel = self.env[model]
            mids = DocumentModel.browse(doc_ids).exists()
            if hasattr(DocumentModel, 'check_mail_message_access'):
                DocumentModel.check_mail_message_access(mids.ids, operation)  # ?? mids ?
            else:
                self.env['mail.thread'].check_mail_message_access(mids.ids, operation, model_name=model)
            document_related_ids += [mid for mid, message in message_values.iteritems()
                                     if message.get('model') == model and message.get('res_id') in mids.ids]

        # Calculate remaining ids: if not void, raise an error
        other_ids = other_ids.difference(set(document_related_ids))
        if not other_ids:
            return
        raise AccessError(
            _(
                'The requested operation cannot be completed due to security restrictions. Please contact your system administrator.\n\n(Document type: %s, Operation: %s)') %
            (self._description, operation))