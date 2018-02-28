# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime

class StockPicking(models.Model):
    _inherit = "stock.picking"

    province = fields.Char(string=u'州／省')
    city = fields.Char(string=u'市')
    street = fields.Char(string=u'街道')
    postal_code = fields.Char(string=u'邮编')
    phone = fields.Char(string=u'电话')
    e_mail = fields.Char(string=u'邮箱')
    shippment_number = fields.Char(string=u'物流单号')

    delivery_date = fields.Datetime(string=u'发货时间')

    own_data = fields.Boolean(search='_own_data_search', store=False)

    merchant_id = fields.Many2one('res.users', string=u'商户')
    country_id = fields.Many2one('amazon.country', string=u'国家')
    logistics_company_id = fields.Many2one('logistics.company', string=u'物流公司')
    sale_order_id = fields.Many2one('sale.order')
    purchase_order_id = fields.Many2one('purchase.order')
    # distributor_invoice_ids = fields.Many2one('invoice', related='sale_order_id.invoice_ids', string=u'经销商发票')

    @api.model
    def _own_data_search(self, operator, value):
        print '_own_data_search stock_picking'
        user = self.env.user
        if user.user_type == 'operator':
            return [('id', '=', 0)]
        elif user.user_type == 'merchant':
            return [('partner_id', '=', user.partner_id.id)]
        else:
            return []

    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     context = self.env.context
    #     if context.get('view_own_data'):
    #         user = self.env.user
    #         if user.user_type == 'operator':
    #             shop_ids = user.shop_ids.ids
    #             args += [('shop_id', 'in', shop_ids)]
    #         elif user.user_type == 'merchant':
    #             shop_ids = []
    #             for operator in user.operator_ids:
    #                 shop_ids += operator.shop_ids.ids
    #             args += [('shop_id', 'in', shop_ids)]
    #     return super(StockPicking, self).search(args, offset, limit, order, count=count)

    @api.multi
    def do_new_transfer(self):
        self.ensure_one()
        result = super(StockPicking, self).do_new_transfer()
        self.delivery_date = datetime.datetime.now()
        self.purchase_order_id.platform_purchase_state = 'done'
        self.sale_order_id.invoice_ids.invoice_confirm()
        self.purchase_order_id.b2b_invoice_ids.invoice_confirm()
        done = True
        for purchase in self.sale_order_id.purchase_orders:
            print purchase
            if purchase.platform_purchase_state != 'done':
                done = False
        print done
        if done:
            self.sale_order_id.b2b_state = 'delivered'
        raise UserError(u'ljp')
        return result

    @api.multi
    def upload_delivery_info(self):
        self.ensure_one()
        # print self.env.context
        # sale_obj = self.env['sale.order']
        # sale_order = sale_obj.search([('procurement_group_id', '=', self.group_id.id)], limit=1)
        return self.sale_order_id.false_delivery()