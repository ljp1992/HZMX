# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ResUsers(models.Model):
    _inherit = 'res.users'

    introduction = fields.Text(u'简介')

    account_amount = fields.Float(string=u'账户余额')
    wait_add = fields.Float(compute='_compute_amount', store=False, string=u'待入账金额')
    wait_reduce = fields.Float(compute='_compute_amount', store=False, string=u'待扣除金额')
    available_cash = fields.Float(compute='_compute_amount', store=False, string=u'可提现金额')

    own_my_data = fields.Boolean(search='_own_my_data', store=False)
    own_user = fields.Boolean(search='_compute_own_user', store=False)

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

    @api.model
    def _compute_own_user(self, operation, value):
        print 1111
        # if self.env.user.id == 1:
        #     return [('user_type', '=', 'management')]
        if self.user_has_groups('b2b_platform.b2b_seller'):
            return [('merchant_id', '=', self.env.user.id)]
        # elif self.user_has_groups('b2b_platform.b2b_manager'):
        #     return [('user_type', '=', 'merchant')]

    @api.multi
    def view_transcation_detail(self):
        self.ensure_one()
        merchant = self.env.user.merchant_id or self.env.user
        return {
            'name': u'交易明细',
            'type': 'ir.actions.act_window',
            'res_model': 'transcation.detail',
            'view_mode': 'tree,',
            'view_type': 'form',
            'views': [
                (self.env.ref('amazon_api.transcation_detail_tree').id, 'tree')],
            'domain': [('merchant_id', '=', merchant.id)],
            'target': 'current',
        }

    @api.multi
    def _compute_amount(self):
        for record in self:
            wait_add = 0
            wait_reduce = 0
            for detail in record.transcation_detail_ids:
                if detail.state == 'draft':
                    if detail.amount < 0:
                        wait_reduce += detail.amount
                    else:
                        wait_add += detail.amount
            record.wait_add = wait_add
            record.wait_reduce = 0 - wait_reduce
            record.available_cash = record.account_amount + wait_reduce

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
    def _own_my_data(self, operator, value):
        user = self.env.user
        if user.user_type == 'operator':
            return [('id', '=', 0)]
        elif user.user_type == 'merchant':
            return [('id', '=', self.env.user.id)]
        else:
            return []

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

