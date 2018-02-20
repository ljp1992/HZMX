# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AmazonMarketplace(models.Model):
    _name = "amazon.marketplace"
    _rec_name = 'country_id'

    name = fields.Char(string=u'name')
    domain_name = fields.Char(string=u'网址')
    marketplace_id = fields.Char(string=u'市场ID')

    seller_ids = fields.Many2many('amazon.seller', 'seller_market_rel', 'market_id', 'seller_id')
    country_id = fields.Many2one('amazon.country', string=u'国家')
    currency_id = fields.Many2one('amazon.currency', string=u'货币')
    currency_symbol = fields.Char(related='currency_id.symbol', string=u'货币符号')
    lang_id = fields.Many2one('amazon.lang', string=u'语言')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args += ('name', operator, name)
        context = self._context

        if context.has_key('seller_id_ljp'):
            seller_id = context['seller_id_ljp']
            if seller_id:
                marketplace_ids = self.env['amazon.seller'].browse(seller_id).marketplace_ids.ids
                args.append(('id', 'in', marketplace_ids))
            else:
                return self.name_get()
        result = self.search(args, limit=limit)
        return result.name_get()

    # @api.multi
    # def create_shop(self):
    #     print self._context
    #     val = {
    #         'name': u'创建店铺',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'amazon.wizard',
    #         'view_mode': 'form',
    #         'view_type': 'form',
    #         'views': [(self.env.ref('amazon_api.create_shop_wizard').id, 'form')],
    #         'target': 'new',
    #     }
    #     print val
    #     return val

    @api.model
    def maintain_amazon_marketplace(self):
        '''initialize amazon marketplace data'''
        marketplace_data = [
            {
                'country_name': u'加拿大',
                'country_code': 'CA',
                'currency_name': 'CAD',
                'currency_symbol': '$',
                'marketplace_id': 'A2EUQ1WTGCTBG2',
                'lang': 'English'
            },
            {
                'country_name': u'美国',
                'country_code': 'US',
                'currency_name': 'USD',
                'currency_symbol': '$',
                'marketplace_id': 'ATVPDKIKX0DER',
                'lang': 'English'
            },
            {
                'country_name': u'墨西哥',
                'country_code': 'MX',
                'currency_name': 'MXN',
                'currency_symbol': '$',
                'marketplace_id': 'A1AM78C64UM0Y8',
                'lang': 'Spanish'
            },
            {
                'country_name': u'德国',
                'country_code': 'DE',
                'currency_name': 'EUR',
                'currency_symbol': '€',
                'marketplace_id': 'A1PA6795UKMFR9',
                'lang': 'German'
            },
            {
                'country_name': u'西班牙',
                'country_code': 'ES',
                'currency_name': 'EUR',
                'currency_symbol': '€',
                'marketplace_id': 'A1RKKUPIHCS9HS',
                'lang': 'Spanish'
            },
            {
                'country_name': u'法国',
                'country_code': 'FR',
                'currency_name': 'EUR',
                'currency_symbol': '€',
                'marketplace_id': 'A13V1IB3VIYZZH',
                'lang': 'French'
            },
            {
                'country_name': u'印度',
                'country_code': 'IN',
                'currency_name': 'INR',
                'currency_symbol': '₹',
                'marketplace_id': 'A21TJRUUN4KGV',
                'lang': 'English'
            },
            {
                'country_name': u'意大利',
                'country_code': 'IT',
                'currency_name': 'EUR',
                'currency_symbol': '€',
                'marketplace_id': 'APJ6JRA9NG5V4',
                'lang': 'Italian'
            },
            {
                'country_name': u'英国',
                'country_code': 'UK',
                'currency_name': 'GBP',
                'currency_symbol': '£',
                'marketplace_id': 'A1F83G8C2ARO7P',
                'lang': 'English'
            },
            {
                'country_name': u'日本',
                'country_code': 'JP',
                'currency_name': 'JPY',
                'currency_symbol': '¥',
                'marketplace_id': 'A1VC38T7YXB528',
                'lang': 'Janpanese'
            },
            {
                'country_name': u'中国',
                'country_code': 'CN',
                'currency_name': 'CNY',
                'currency_symbol': '¥',
                'marketplace_id': 'AAHKV2X7AFYLW',
                'lang': 'Chinese'
            },
        ]
        country_obj = self.env['amazon.country']
        currency_obj = self.env['amazon.currency']
        lang_obj = self.env['amazon.lang']
        market_obj = self.env['amazon.marketplace']
        for item in marketplace_data:
            country = country_obj.search([('code', '=', item['country_code'])], limit=1)
            if not country:
                country = country_obj.create({'name': item['country_name'], 'code': item['country_code']})
            currency = currency_obj.search([('name', '=', item['currency_name'])], limit=1)
            if not currency:
                currency = currency_obj.create({'name': item['currency_name'], 'symbol': item['currency_symbol']})
            lang = lang_obj.search([('name', '=', item['lang'])], limit=1)
            if not lang:
                lang = lang_obj.create({'name': item['lang']})
            market = market_obj.search([('country_id', '=', country.id)], limit=1)
            if market:
                market.write({
                    'currency_id': currency.id,
                    'lang_id': lang.id,
                    'marketplace_id': item['marketplace_id'],
                })
            else:
                market_obj.create({
                    'country_id': country.id,
                    'currency_id': currency.id,
                    'lang_id': lang.id,
                    'marketplace_id': item['marketplace_id'],
                })

