# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ResUsers(models.Model):
    _inherit = 'res.users'

    introduction = fields.Text(u'简介')

    merchant_id = fields.Many2one('res.users', string=u'商户')

    operator_ids = fields.One2many('res.users', 'merchant_id', string=u'操作员')

    user_type = fields.Selection([
        ('operator', u'操作员'),
        ('merchant', u'商户'),
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
        self.write({
            'groups_id': [(6, False, [self.env.ref('b2b_platform.b2b_seller').id])],
            'audit_state': 'pass',
        })
        location_obj = self.env['stock.location']
        partner_id = self.partner_id.id
        location_id = self.env.ref('b2b_platform.supplier_stock').id
        location = location_obj.search([('partner_id', '=', partner_id), ('location_id', '=', location_id)])
        if not location:
            location_obj.create({
                'name': self.name,
                'location_id': location_id,
                'partner_id': partner_id,
            })

    @api.model
    def create(self, val):
        '''设置默认密码为123'''
        context = self.env.context
        print context
        if context.get('user_type') == 'management':
            val.update({
                'user_type': 'management',
                'groups_id': [(4, self.env.ref('b2b_platform.b2b_manager').id)],
                'password': 123,
            })
        elif context.get('user_type') == 'operator':
            val.update({
                'user_type': 'operator',
                'merchant_id': self.env.user.id,
                'groups_id': [(4, self.env.ref('b2b_platform.b2b_shop_operator').id)],
                'password': 123,
            })
        user = super(ResUsers, self).create(val)
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

    # @api.model
    # def return_operator_view(self):
    #     user = self.env.user
    #     if user.user_type == 'operator':
    #         return {}
    #     elif user.user_type == 'merchant':
    #         domain = [('user_type', '=', 'operator'),('merchant_id', '=', user.id)]
    #     else:
    #         domain = [('user_type', '=', 'operator')]
    #     val = {
    #         'type': 'ir.actions.act_window',
    #         'name': u'店铺操作员',
    #         'view_mode': 'tree,form',
    #         'view_type': 'form',
    #         'views': [(self.env.ref('b2b_platform.b2b_operator_tree').id, 'tree'),
    #                   (self.env.ref('b2b_platform.b2b_operator_form').id, 'form')],
    #         'res_model': 'res.users',
    #         'domain': domain,
    #         'context': {'default_user_type': 'operator'},
    #         'target': 'current',
    #     }
    #     return val

