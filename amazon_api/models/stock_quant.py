# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    own_data = fields.Boolean(compute='_compute_own_data', search='_own_data', default=False, store=False)
    own_prodcut_quant = fields.Boolean(search='_own_prodcut_quant', store=False)

    @api.model
    def _own_prodcut_quant(self, operation, value):
        if self.user_has_groups('b2b_platform.b2b_shop_operator') or \
                self.user_has_groups('b2b_platform.b2b_seller'):
            merchant = self.env.user.merchant_id or self.env.user
            distributor_tmpls = self.env['product.template'].sudo().search([
                ('state', '=', 'seller'),
                ('merchant_id', '=', merchant.id),
            ])
            product_ids = []
            for distributor_tmpl in distributor_tmpls:
                product_ids += distributor_tmpl.platform_tmpl_id.product_variant_ids.ids
            quants = self.env['stock.quant'].search([
                ('product_id', 'in', product_ids),
                ('location_id.usage', '=', 'internal'),
            ])
            return [('id', 'in', quants.ids)]

    @api.multi
    def _compute_own_data(self):
        merchant = self.env.user.merchant_id or self.env.user
        if self.user_has_groups('b2b_platform.b2b_shop_operator'):
            products = self.env['product.product'].search([
                ('state', '=', 'platform_published'),
                ('merchant_id', '=', merchant.id),
            ])
        elif self.user_has_groups('b2b_platform.b2b_seller'):
            products = self.env['product.product'].search([
                ('state', '=', 'platform_published'),
                ('merchant_id', '=', merchant.id),
            ])
        else:
            products = self.env['product.product'].search([
                ('state', '=', 'platform_published'),
            ])
        for record in self:
            if record.product in products:
                record.own_data = True
            else:
                record.own_data = False

    @api.model
    def _own_data(self, operation, value):
        print 'field search'
        merchant = self.env.user.merchant_id or self.env.user
        products = self.env['product.product'].search([
            ('state', '=', 'platform_published'),
            ('merchant_id', '=', merchant.id),
        ])
        locs = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('partner_id', '=', merchant.partner_id.id),
        ])
        quants = self.env['stock.quant'].search([
            ('product_id', 'in', products.ids),
            ('location_id', 'in', locs.ids),
        ])
        print products,locs
        if self.user_has_groups('b2b_platform.b2b_shop_operator'):
            return [('id', 'in', quants.ids)]
        elif self.user_has_groups('b2b_platform.b2b_seller'):
            return [('id', 'in', quants.ids)]
        else:
            return []

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100):
    #     args = args or []
    #     if name:
    #         args += [('name', operator, name)]
    #     result = self.search(args, limit=limit)
    #     return result.name_get()
    #
    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     print 11111111
    #     context = self.env.context or {}
    #     print context,context.get('view_own_quant')
    #     if context.get('view_own_quant'):
    #         merchant = self.env.user.merchant_id or self.env.user
    #         products = self.env['product.product'].search([
    #             ('state', '=', 'platform_published'),
    #             ('merchant_id', '=', merchant.id),
    #         ])
    #         print products
    #         if self.user_has_groups('b2b_platform.b2b_shop_operator'):
    #             args += [('product_id', 'in', products.ids)]
    #         elif self.user_has_groups('b2b_platform.b2b_seller'):
    #             args += [('product_id', 'in', products.ids)]
    #         elif self.user_has_groups('b2b_platform.b2b_manager'):
    #             pass
    #         else:
    #             pass
    #     return super(StockQuant, self).search(args, offset, limit, order, count=count)