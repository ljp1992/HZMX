# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AmazonShop(models.Model):
    _name = "amazon.shop"

    name = fields.Char(string=u'名称', required=True)
    currency_symbol = fields.Char(related='currency_id.symbol', string=u'货币', store=False, readonly=True)

    rate = fields.Float(string=u'上浮率(%)')

    seller_id = fields.Many2one('amazon.seller', string=u'卖家', required=True)
    marketplace_id = fields.Many2one('amazon.marketplace', string=u'市场', required=True)
    currency_id = fields.Many2one('amazon.currency', related='marketplace_id.currency_id', string=u'货币', store=False,
                                  readonly=1)
    country_id = fields.Many2one('amazon.country', related='marketplace_id.country_id', string=u'国家')
    lang_id = fields.Many2one('amazon.lang', related='marketplace_id.lang_id', string=u'语言', store=False, readonly=1)
    operator_id = fields.Many2one('res.users', default=lambda self: self.env.user, inverse='_set_operator_tmpl_rule',
                                  string=u'操作员')
    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user,
                                  string=u'商户')

    @api.multi
    def _set_operator_tmpl_rule(self):
        '''odoo 记录规则bug 当定义了one2many字段放在记录规则里面出问题，需要执行rule write方法，one2many的值才会更新 '''
        self.env.ref('amazon_api.product_template_operator_rule4').name = 'product_template_operator_rule4'
        self.env.ref('amazon_api.product_template_merchant_rule1').name = 'product_template_merchant_rule1'
        self.env.ref('amazon_api.submission_history_operator_rule').name = 'submission_history_operator_rule'
        # self.env.ref('amazon_api.sale_order_operator_rule').name = 'sale_order_operator_rule'

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100):
    #     args = args or []
    #     args += [('name', operator, name)]
    #     user = self.env.user
    #     if user.user_type == 'operator':
    #         args += [('operator_id', '=', user.id)]
    #     elif user.user_type == 'merchant':
    #         args += [('merchant_id', '=', user.id)]
    #     print args
    #     # args = list(set(args))
    #     result = self.search(args, limit=limit)
    #     return result.name_get()

    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     user = self.env.user
    #     if user.user_type == 'operator':
    #         args += [('operator_id', '=', user.id)]
    #     elif user.user_type == 'merchant':
    #         args += [('merchant_id', '=', user.id)]
    #     # args = list(set(args))
    #     return super(AmazonShop, self).search(args, offset, limit, order, count=count)

    @api.model
    def create(self, val):
        seller = super(AmazonShop, self).create(val)
        seller.check_shop()
        return seller

    @api.multi
    def write(self, val):
        result = super(AmazonShop, self).write(val)
        self.check_shop()
        return result

    @api.multi
    def check_shop(self):
        '''检查店铺信息是否合法'''
        for shop in self:
            if shop.marketplace_id not in shop.seller_id.marketplace_ids:
                raise UserError(u'该卖家没有该市场！')
            results = self.env['amazon.shop'].search([
                ('seller_id', '=', shop.seller_id.id),
                ('marketplace_id', '=', shop.marketplace_id.id)
            ])
            if len(results) > 1:
                raise UserError(u'系统中已存在该卖家该市场的店铺！')

    # @api.model
    # def return_act_view(self):
    #     domain = []
    #     user = self.env.user
    #     if user.user_type == 'operator':
    #         domain = [('operator_id', '=', user.id)]
    #     elif user.user_type == 'merchant':
    #         domain = [('merchant_id', '=', user.id)]
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': u'店铺',
    #         'view_mode': 'tree,form',
    #         'view_type': 'form',
    #         'views': [(self.env.ref('amazon_api.amazon_shop_tree').id, 'tree'),
    #                   (self.env.ref('amazon_api.amazon_shop_form').id, 'form')],
    #         'res_model': 'amazon.shop',
    #         'domain': domain,
    #         'target': 'current',
    #     }