# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.addons.amazon_api.amazon_api.mws import Sellers

class AmazonSeller(models.Model):
    _name = "amazon.seller"

    name = fields.Char(string=u'名称', required=True)
    access_key = fields.Char(string='访问密钥', required=True)
    secret_key = fields.Char(string=u'密钥', required=True)
    merchant_id_num = fields.Char(string=u'商家ID', required=True)

    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user,
                                  string=u'商户')

    shop_ids = fields.One2many('amazon.shop', 'seller_id', string=u'店铺')

    marketplace_ids = fields.Many2many('amazon.marketplace', 'seller_market_rel', 'seller_id', 'market_id',)

    # @api.model
    # def _default_merchant_id(self):
    #     partner = self.env.user.partner_id
    #     if partner.parent_id:
    #         return partner.parent_id.id
    #     else:
    #         return partner.id

    @api.model
    def create(self, val):
        seller = super(AmazonSeller, self).create(val)
        return seller

    @api.multi
    def write(self, val):
        result = super(AmazonSeller, self).write(val)
        return result

    @api.multi
    def unlink(self):
        for seller in self:
            if seller.shop_ids:
                raise UserError(u'请先删除店铺！')
        return super(AmazonSeller, self).unlink()

    @api.multi
    def load_marketplace(self):
        '''create marketplaces of seller'''
        marketplace_obj = self.env['amazon.marketplace']
        for seller in self:
            marketplaces = []
            mws_obj = Sellers(access_key=str(seller.access_key), secret_key=str(seller.secret_key),
                              account_id=str(seller.merchant_id_num))
            try:
                result = mws_obj.list_marketplace_participations()
                marketplaces.append(result.parsed)
            except Exception, e:
                raise UserError(str(e))
            next_token = result.parsed.get('NextToken', {}).get('value')
            while next_token:
                try:
                    result = mws_obj.list_marketplace_participations_by_next_token(next_token)
                    marketplaces.append(result.parsed)
                except Exception, e:
                    raise UserError(str(e))
                next_token = result.parsed.get('NextToken', {}).get('value')
            marketplace_ids = []
            print marketplaces
            for marketplace in marketplaces:
                print marketplace
                for item in marketplace.get('ListMarketplaces', {}).get('Marketplace', []):
                    marketplace_id = item.get('MarketplaceId', {}).get('value', '')
                    marketplace = marketplace_obj.search([('marketplace_id', '=', marketplace_id)])
                    if not marketplace:
                        continue
                        raise UserError(u'Not found marketplace_id %s in amazon.marketplace model!' % marketplace_id)
                    if marketplace:
                        marketplace_ids.append(marketplace.id)
            seller.marketplace_ids = [(6, False, marketplace_ids)]

    # @api.model
    # def return_act_view(self):
    #     domain = []
    #     user = self.env.user
    #     if user.user_type == 'merchant':
    #         domain = [('merchant_id', '=', user.id)]
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': u'卖家',
    #         'view_mode': 'tree,form',
    #         'view_type': 'form',
    #         'views': [(self.env.ref('amazon_api.amazon_seller_tree').id, 'tree'),
    #                   (self.env.ref('amazon_api.amazon_seller_form').id, 'form')],
    #         'res_model': 'amazon.seller',
    #         'domain': domain,
    #         'target': 'current',
    #     }

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100):
    #     args = args or []
    #     if name:
    #         args += ('name', operator, name)
    #     user = self.env.user
    #     if user.user_type == 'operator':w
    #         args.append(('merchant_id', '=', user.merchant_id.id))
    #     elif user.user_type == 'merchant':
    #         args.append(('merchant_id', '=', user.id))
    #     result = self.search(args, limit=limit)
    #     return result.name_get()
