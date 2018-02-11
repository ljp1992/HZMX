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

    marketplace_ids = fields.Many2many('amazon.marketplace', 'seller_market_rel', 'seller_id', 'market_id',)

    # @api.model
    # def create(self, val):
    #     seller = super(AmazonSeller, self).create(val)
    #     seller.load_marketplace()
    #     return seller
    #
    # @api.multi
    # def write(self, val):
    #     result = super(AmazonSeller, self).write(val)
    #     self.load_marketplace()
    #     return result
    #
    # @api.multi
    # def load_marketplace(self):
    #     '''create marketplaces of seller'''
    #     country_obj = self.env['res.country']
    #     currency_obj = self.env['res.currency']
    #     lang_obj = self.env['res.lang']
    #     marketplace_obj = self.env['amazon.marketplace']
    #     for seller in self:
    #         marketplaces = []
    #         mws_obj = Sellers(access_key=str(seller.access_key), secret_key=str(seller.secret_key),
    #                           account_id=str(seller.merchant_id))
    #         try:
    #             result = mws_obj.list_marketplace_participations()
    #             marketplaces.append(result.parsed)
    #         except Exception, e:
    #             raise UserError(str(e))
    #         next_token = result.parsed.get('NextToken', {}).get('value')
    #         while next_token:
    #             try:
    #                 result = mws_obj.list_marketplace_participations_by_next_token(next_token)
    #                 marketplaces.append(result.parsed)
    #             except Exception, e:
    #                 raise UserError(str(e))
    #             next_token = result.parsed.get('NextToken', {}).get('value')
    #         for marketplace in marketplaces:
    #             for item in marketplace.get('ListMarketplaces', {}).get('Marketplace', []):
    #                 name = item.get('Name', {}).get('value', '')
    #                 domain_name = item.get('DomainName', {}).get('value', '')
    #                 marketplace_id = item.get('MarketplaceId', {}).get('value', '')
    #                 country_code = item.get('DefaultCountryCode', {}).get('value', '')
    #                 currency_code = item.get('DefaultCurrencyCode', {}).get('value', '')
    #                 lang_code = item.get('DefaultLanguageCode', {}).get('value', '')
    #                 country_id = country_obj.search([('code', '=', country_code)]).id or False
    #                 print currency_code,type(currency_code),currency_obj.search([('name', '=', 'CAD')])
    #                 currency_id = currency_obj.search([('name', '=', currency_code)]).id or False
    #                 print currency_id
    #                 lang_id = lang_obj.search([('code', '=', lang_code)]).id or False
    #                 result = marketplace_obj.search([
    #                     ('seller_id', '=', seller.id),
    #                     ('marketplace_id', '=', marketplace_id),
    #                 ])
    #                 if result:
    #                     result.write({
    #                         'name': name,
    #                         'domain_name': domain_name,
    #                         'country_id': country_id,
    #                         'currency_id': currency_id,
    #                         'lang_id': lang_id,
    #                     })
    #                 else:
    #                     marketplace_obj.create({
    #                         'seller_id': seller.id,
    #                         'name': name,
    #                         'domain_name': domain_name,
    #                         'marketplace_id': marketplace_id,
    #                         'country_id': country_id,
    #                         'currency_id': currency_id,
    #                         'lang_id': lang_id,
    #                     })