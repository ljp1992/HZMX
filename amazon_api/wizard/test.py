# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime
from odoo.addons.amazon_api.amazon_api.mws import Products

class Test(models.TransientModel):
    _name = "test"

    name = fields.Char(required=True, string=u'编码')

    result = fields.Text(string=u'返回结果')

    shop_id = fields.Many2one('amazon.shop', required=True, string=u'店铺')

    type = fields.Selection([
        ('UPC', u'UPC'),
        ('ASIN', u'ASIN'),
        ('SellerSKU', u'SellerSKU'),
    ], default='UPC', required=True, string=u'类型')

    @api.multi
    def get_product_info(self):
        '''获取产品信息'''
        self.ensure_one()
        shop = self.shop_id
        seller = shop.seller_id
        marketplace_id = shop.marketplace_id.marketplace_id
        ids = [self.name]
        mws_obj = Products(access_key=str(seller.access_key), secret_key=str(seller.secret_key),
                           account_id=str(seller.merchant_id_num), region=shop.country_id.code, proxies={})
        if self.type == 'SellerSKU':
            result = mws_obj.get_matching_product_for_id(marketplaceid=marketplace_id, type='SellerSKU', ids=ids)
        elif self.type == 'UPC':
            result = mws_obj.list_matching_products(marketplaceid=marketplace_id, query=self.name, contextid=None)
        elif self.type == 'ASIN':
            result = mws_obj.get_matching_product_for_id(marketplaceid=marketplace_id, type='ASIN', ids=ids)
        self.result = result.parsed
