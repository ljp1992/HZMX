# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from lxml import etree

class StockLocation(models.Model):
    _inherit = "stock.location"

    partner_id = fields.Many2one('res.partner', domain=lambda self: self._partner_id_domain(), string=u'所有人')
    location_id = fields.Many2one('stock.location', default=lambda self: self._paltform_location())

    @api.model
    def return_merchant_supplier_location(self, merchant):
        return self.env['stock.location'].sudo().search([
            ('partner_id', '=', merchant.partner_id.id),
            ('location_id', '=', self.env.ref('b2b_platform.supplier_stock').id)], limit=1)

    @api.model
    def return_merchant_third_location(self, merchant):
        return self.env['stock.location'].sudo().search([
            ('partner_id', '=', merchant.partner_id.id),
            ('location_id', '=', self.env.ref('b2b_platform.third_warehouse').id)], limit=1)


    @api.model
    def _paltform_location(self):
        if self.user_has_groups('b2b_platform.b2b_manager'):
            return self.env.ref('b2b_platform.third_warehouse').id

    @api.model
    def _partner_id_domain(self):
        if self.user_has_groups('b2b_platform.b2b_manager'):
            users = self.env['res.users'].search([('user_type', '=', 'merchant')])
            partner_ids = [user.partner_id.id for user in users]
            return [('id', 'in', partner_ids)]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args += [('name', operator, name)]
        result = self.search(args, limit=limit)
        return result.name_get()


    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self.env.context or {}
        if context.get('view_own_data'):
            if self.user_has_groups('b2b_platform.b2b_shop_operator'):
                args += [('partner_id', '=', self.env.user.merchant_id.partner_id.id)]
            elif self.user_has_groups('b2b_platform.b2b_seller'):
                args += [('partner_id', '=', self.env.user.partner_id.id)]
            elif self.user_has_groups('b2b_platform.b2b_manager'):
                pass
            else:
                pass
        return super(StockLocation, self).search(args, offset, limit, order, count=count)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(StockLocation, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                          submenu=submenu)
        if view_type == 'tree' and self.user_has_groups('b2b_platform.b2b_manager'):
            print res['arch']
            res['arch'] = res['arch'].replace('<tree create="0" edit="0" delete="0">', '<tree>')
        elif view_type == 'form' and self.user_has_groups('b2b_platform.b2b_manager'):
            res['arch'] = res['arch'].replace('<form create="0" edit="0" delete="0">', '<form>')

        return res


