# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ResUsers(models.Model):
    _inherit = 'res.users'

    introduction = fields.Text(u'简介')

    user_type = fields.Selection([
        ('merchant', u'店主'),
        ('operator', u'操作员'),
        ('management', u'平台管理员'),
    ], string=u'账号类型')
    audit_state = fields.Selection([
        ('waiting', u'待审核'),
        ('pass', u'审核通过'),
        ('failed', u'未审核通过')
    ], string=u'审核状态')

    @api.multi
    def pass_audit(self):
        '''审核通过'''
        self.ensure_one()
        self.groups_id = [(6, False, [self.env.ref('b2b_platform.b2b_seller').id])]
        self.audit_state = 'pass'

    @api.model
    def create(self, val):
        '''设置默认密码为123'''
        print 'create:',val
        user = super(ResUsers, self).create(val)
        if user.user_type == 'management':
            user.groups_id = [(4, self.env.ref('b2b_platform.b2b_manager').id)]
            user.password = '123'
        return user


    # def unlink(self):
    #     '''删除user，同时也删除partner'''
    #     partner_ids = []
    #     for user in self:
    #         partner_ids.append(user.partner_id.id)
    #     partners = self.env['res.partner'].browse(partner_ids)
    #     print partners
    #     result = super(ResUsers, self).unlink()
    #     print partners
    #     partners.unlink()
    #     print partners
    #     raise UserError('11')
    #     return result