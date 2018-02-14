# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.addons.amazon_api.amazon_api.mws import Sellers

class AmazonSeller(models.Model):
    _name = "amazon.seller"

    name = fields.Char(string=u'名称', required=True)
    access_key = fields.Char(string='访问密钥', required=True)
    secret_key = fields.Char(string=u'密钥', required=True)
    merchant_id = fields.Char(string=u'商家ID', required=True)

    shop_ids = fields.One2many('amazon.shop', 'seller_id', string=u'店铺')

    marketplace_ids = fields.Many2many('amazon.marketplace', 'seller_market_rel', 'seller_id', 'market_id',)

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
                              account_id=str(seller.merchant_id))
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
            for marketplace in marketplaces:
                for item in marketplace.get('ListMarketplaces', {}).get('Marketplace', []):
                    marketplace_id = item.get('MarketplaceId', {}).get('value', '')
                    marketplace = marketplace_obj.search([('marketplace_id', '=', marketplace_id)])
                    if not marketplace:
                        raise UserError(u'Not found marketplace_id %s in amazon.marketplace model!' % marketplace_id)
                    if marketplace:
                        marketplace_ids.append(marketplace.id)
            seller.marketplace_ids = [(6, False, marketplace_ids)]
