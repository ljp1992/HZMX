# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AmazonShop(models.Model):
    _name = "amazon.shop"

    name = fields.Char(string=u'名称', required=True)
    currency_symbol = fields.Char(related='currency_id.symbol', string=u'货币', store=False, readonly=True)

    seller_id = fields.Many2one('amazon.seller', string=u'卖家', required=True)
    marketplace_id = fields.Many2one('amazon.marketplace', string=u'市场', required=True)
    currency_id = fields.Many2one('amazon.currency', related='marketplace_id.currency_id', string=u'货币', store=False,
                                  readonly=1)
    lang_id = fields.Many2one('amazon.lang', related='marketplace_id.lang_id', string=u'语言', store=False, readonly=1)
    operator_id = fields.Many2one('res.users', default=lambda self: self.env.user,
                                  domain=lambda self: ['|',('id', '=', self.env.user.id),
                                                       ('merchant_id', '=', self.env.user.id)], string=u'操作员')
    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user,
                                  string=u'商户')

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

    @api.model
    def return_act_view(self):
        domain = []
        user = self.env.user
        if user.user_type == 'operator':
            domain = [('operator_id', '=', user.id)]
        elif user.user_type == 'merchant':
            domain = [('merchant_id', '=', user.id)]
        return {
            'type': 'ir.actions.act_window',
            'name': u'店铺',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [(self.env.ref('amazon_api.amazon_shop_tree').id, 'tree'),
                      (self.env.ref('amazon_api.amazon_shop_form').id, 'form')],
            'res_model': 'amazon.shop',
            'domain': domain,
            'target': 'current',
        }