# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime
from odoo.addons.amazon_api.amazon_api.mws import Feeds

class SaleOrder(models.Model):
    _inherit = "sale.order"

    e_order = fields.Char(string=u'电商订单号')
    province = fields.Char(string=u'州／省')
    city = fields.Char(string=u'市')
    street = fields.Char(string=u'街道')
    postal_code = fields.Char(string=u'邮编')
    phone = fields.Char(string=u'电话')
    e_mail = fields.Char(string=u'邮箱')
    e_currency_id1 = fields.Char(related='e_currency_id.symbol', string=u'币种')
    e_currency_id2 = fields.Char(related='e_currency_id.symbol', string=u'币种')
    e_currency_id3 = fields.Char(related='e_currency_id.symbol', string=u'币种')

    sale_date = fields.Datetime(string=u'下单日期')
    confirm_date = fields.Datetime(string=u'确认日期')

    b2b_delivery_count = fields.Integer(compute='_b2b_delivery_count')
    purchase_count = fields.Integer(compute='_purchase_count')
    invoice_count = fields.Integer(compute='_invoice_count')

    e_order_amount = fields.Float(string=u'订单金额')
    e_order_freight = fields.Float(compute='_e_order_freight', store=False, string=u'运费')
    e_order_commission = fields.Float(compute='_e_order_commission', store=False, string=u'佣金')

    # own_data = fields.Boolean(compute='_get_own_data', search='_own_data_search')
    have_own_product = fields.Boolean(compute='_have_own_product', default=False, help=u'单据是否有自有产品')
    have_not_own_product = fields.Boolean(compute='_have_own_product', default=False, help=u'单据是否有非自有产品')
    had_own_delivery = fields.Boolean(compute='_had_b2b_delivery', default=False, help=u'已经操作过自有发货了')
    had_agent_delivery = fields.Boolean(compute='_had_b2b_delivery', default=False, help=u'已经操作过平台采购了')
    own_data = fields.Boolean(search='_own_data_search', store=False)
    hide_platform_purchase_button = fields.Boolean(compute='_hide_platform_purchase_button', string=u'隐藏平台采购按钮')
    hide_myself_delivery_button = fields.Boolean(compute='_hide_myself_delivery_button', string=u'隐藏自有发货按钮')

    country_id = fields.Many2one('amazon.country', string=u'国家')
    shop_id = fields.Many2one('amazon.shop', string=u'店铺')
    e_currency_id = fields.Many2one('amazon.currency', related='shop_id.currency_id', string=u'币种')
    operator_id = fields.Many2one('res.users', default=lambda self: self.env.user, string=u'操作员')
    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user,
                                  string=u'商户')

    purchase_orders = fields.One2many('purchase.order', 'sale_order_id')
    deliverys = fields.One2many('stock.picking', 'sale_order_id', domain=[('b2b_type', '=', 'outgoing')],
                                string=u'发货单')
    own_deliverys = fields.One2many('stock.picking', 'sale_order_id', domain=[
        ('b2b_type', '=', 'outgoing'),
        ('origin_type', '=', 'own_delivery')], string=u'自有发货单')
    agent_deliverys = fields.One2many('stock.picking', 'sale_order_id', domain=[
        ('b2b_type', '=', 'outgoing'),
        ('origin_type', '=', 'agent_delivery')], string=u'代理发货单')
    transfer_pickings = fields.One2many('stock.picking', 'sale_order_id', domain=[('b2b_type', '=', 'internal')],
                                        string=u'调拨单')
    b2b_invoice_ids = fields.One2many('invoice', 'sale_order_id', string=u'发票')

    platform = fields.Selection([
        ('amazon', u'亚马逊'),
        ('ebay', u'Ebay')], default='amazon', string=u'来源平台')
    delivery_mode = fields.Selection([
        ('MFN', u'自发货'),
        ('FBA', u'FBA')], default='MFN', string=u'运输方式')
    amazon_state = fields.Selection([
        ('PendingAvailability', u'PendingAvailability'),
        ('Pending', u'Pending'),
        ('Unshipped', u'Unshipped'),
        ('PartiallyShipped', u'PartiallyShipped'),
        ('Shipped', u'Shipped'),
        ('InvoiceUnconfirmed', u'InvoiceUnconfirmed'),
        ('Canceled', u'Canceled'),
        ('Unfulfillable', u'Unfulfillable'),
    ], string=u'亚马逊订单状态')
    shipment_service_level_category = fields.Selection([
        ('Expedited', 'Expedited'),
        ('NextDay', 'NextDay'),
        ('SecondDay', 'SecondDay'),
        ('Standard', 'Standard'),
        ('FreeEconomy', 'FreeEconomy')], string=u"货运服务等级", default='Standard')
    delivery_upload_state = fields.Selection([
        ('wait_upload', u'待上传'),
        ('uploading', u'正在上传'),
        ('done', u'完成'),
        ('failed', u'失败')], default='wait_upload', string=u'发货信息上传状态')
    b2b_state = fields.Selection([
        ('wait_handle', u'待处理'),
        ('delivering', u'待发货'),
        ('delivered', u'已交付'),
        ('cancel', u'取消')], default='wait_handle', string=u'状态')
    b2b_type = fields.Selection([
        ('own_delivery', u'自有发货'),
        ('agent_delivery', u'代发采购'),
        ('own_and_agent_delivery', u'自有发货&代发采购')], string=u'类型')

    @api.multi
    def _had_b2b_delivery(self):
        for record in self:
            if record.own_deliverys:
                record.had_own_delivery = True
            if record.agent_deliverys:
                record.had_agent_delivery = True

    @api.multi
    def _have_own_product(self):
        for record in self:
            for line in record.order_line:
                if line.own_product:
                    record.have_own_product = True
                else:
                    record.have_not_own_product = True

    @api.multi
    def judge_sale_order_type(self):
        '''判断单据是自有发货、代发采购、还是既有自有发货又有代发采购'''
        for record in self:
            if record.have_own_product and record.have_not_own_product:
                record.b2b_type = 'own_and_agent_delivery'
            elif record.have_own_product:
                record.b2b_type = 'own_delivery'
            elif record.have_not_own_product:
                record.b2b_type = 'agent_delivery'
            else:
                record.b2b_type = ''

    @api.multi
    def _b2b_delivery_count(self):
        for record in self:
            record.b2b_delivery_count = len(record.own_deliverys) + len(record.agent_deliverys)

    def _invoice_count(self):
        for record in self:
            record.invoice_count = len(record.b2b_invoice_ids)

    @api.multi
    def view_delivery_order(self):
        self.ensure_one()
        return {
            'name': u'发货单',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [(self.env.ref('amazon_api.stock_picking_tree').id, 'tree'),
                      (self.env.ref('amazon_api.b2b_stock_picking_form').id, 'form')],
            'domain': [('id', 'in', self.own_deliverys.ids + self.agent_deliverys.ids)],
            'target': 'current',
        }

    def view_invoice(self):
        self.ensure_one()
        return {
            'name': u'经销商发票',
            'type': 'ir.actions.act_window',
            'res_model': 'invoice',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [
                (self.env.ref('b2b_platform.invoice_tree').id, 'tree'),
                (self.env.ref('b2b_platform.invoice_form').id, 'form')],
            'domain': [('sale_order_id', '=', self.id)],
            'target': 'current',
        }

    @api.multi
    def view_purchase_order(self):
        return {
            'name': u'采购单',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [
                (self.env.ref('amazon_api.purchase_order_tree').id, 'tree'),
                (self.env.ref('purchase.purchase_order_form').id, 'form')],
            'domain': [('id', 'in', self.purchase_orders.ids)],
            'target': 'current',
        }

    @api.multi
    def _purchase_count(self):
        for order in self:
            order.purchase_count = len(order.purchase_orders)

    @api.multi
    def _e_order_commission(self):
        for order in self:
            order.e_order_commission = order.e_order_amount * 0.15

    @api.multi
    def _e_order_freight(self):
        for order in self:
            freight = 0
            for line in order.order_line:
                freight += line.e_freight
            order.e_order_freight = freight

    @api.multi
    def _hide_platform_purchase_button(self):
        for order in self:
            hide_platform_purchase_button = True
            for line in order.order_line:
                if not line.own_product:
                    hide_platform_purchase_button = False
                    break
            if order.purchase_count > 0:
                hide_platform_purchase_button = True
            order.hide_platform_purchase_button = hide_platform_purchase_button

    @api.multi
    def _hide_myself_delivery_button(self):
        for order in self:
            order.hide_myself_delivery_button = True
            for line in order.order_line:
                if line.own_product:
                    order.hide_myself_delivery_button = False


    @api.multi
    def false_delivery(self):
        '''假发货'''
        self.ensure_one()
        return {
            'name': u'假发货',
            'type': 'ir.actions.act_window',
            'res_model': 'amazon.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(self.env.ref('amazon_api.false_delivery_wizard').id, 'form')],
            'target': 'new',
        }

    @api.multi
    def b2b_action_confirm(self):
        '''自有产品生成发货单'''
        self.ensure_one()
        # if self.own_deliverys:
        #     raise UserError(u'已经生成了发货单！')
        stock_picking_obj = self.env['stock.picking']
        loc_obj = self.env['stock.location']
        merchant = self.env.user.merchant_id or self.env.user
        location = loc_obj.search([
            ('partner_id', '=', merchant.partner_id.id),
            ('location_id', '=', self.env.ref('b2b_platform.third_warehouse').id)], limit=1)
        if not location:
            location = loc_obj.search([
                ('partner_id', '=', merchant.partner_id.id),
                ('location_id', '=', self.env.ref('b2b_platform.supplier_stock').id)], limit=1)
        if not location:
            raise UserError(u'Not found supplier b2b location!')
        location_dest_id = self.env.ref('stock.stock_location_customers').id
        val = {
            'partner_id': merchant.partner_id.id,
            'merchant_id': merchant.id,
            'location_id': location.id,
            'location_dest_id': location_dest_id,
            'picking_type_id': 4,
            'b2b_type': 'outgoing',
            'origin_type': 'own_delivery',
            'origin': self.name,
            'sale_order_id': self.id,
            'pack_operation_product_ids': [],
        }
        for line in self.order_line:
            val['pack_operation_product_ids'].append((0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.product_uom_qty,
                'qty_done': line.product_uom_qty,
                'product_uom_id': line.product_uom.id,
                'location_id': location.id,
                'location_dest_id': location_dest_id,
                'b2b_sale_line_id': line.id,
            }))
        delivery = stock_picking_obj.create(val)
        delivery.create_delivery_info()
        self.b2b_state = 'delivering'
        return {
            'name': u'自有产品发货',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [(self.env.ref('amazon_api.stock_picking_tree').id, 'tree'),
                      (self.env.ref('amazon_api.b2b_stock_picking_form').id, 'form')],
            'domain': [('id', '=', delivery.id)],
            'target': 'current',
        }

    # @api.multi
    # def _get_own_data(self):
    #     print '_get_own_data'
    #     user = self.env.user
    #     for record in self:
    #         if user.user_type == 'operator':
    #             if record.shop_id in user.shop_ids.ids:
    #                 record.own_data = True
    #             else:
    #                 record.own_data = False
    #         elif user.user_type == 'merchant':
    #             shop_ids = []
    #             for operator in user.operator_ids:
    #                 shop_ids += operator.shop_ids.ids
    #             if record.shop_id in shop_ids:
    #                 record.own_data = True
    #             else:
    #                 record.own_data = False

    @api.model
    def _own_data_search(self, operator, value):
        user = self.env.user
        if user.user_type == 'operator':
            return [('shop_id', 'in', user.shop_ids.ids)]
        elif user.user_type == 'merchant':
            shop_ids = []
            for operator in user.operator_ids:
                shop_ids += operator.shop_ids.ids
            return [('shop_id', 'in', shop_ids)]
        else:
            return []

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
        if context.get('view_own_sale_order'):
            if self.user_has_groups('b2b_platform.b2b_shop_operator'):
                args += [('shop_id', 'in', self.env.user.shop_ids.ids)]
            elif self.user_has_groups('b2b_platform.b2b_seller'):
                seller_ids = self.env['amazon.seller'].search([('merchant_id', '=', self.env.user.id)]).ids
                shop_ids = self.env['amazon.shop'].search([('seller_id', 'in', seller_ids)]).ids
                print shop_ids
                args += [('shop_id', 'in', shop_ids)]
            elif self.user_has_groups('b2b_platform.b2b_manager'):
                pass
            else:
                pass
        print args
        return super(SaleOrder, self).search(args, offset, limit, order, count=count)

    @api.multi
    def platform_purchase(self):
        '''平台采购'''
        self.ensure_one()
        self.b2b_state = 'delivering'
        purchase_obj = self.env['purchase.order']
        loc_obj = self.env['stock.location']
        stock_picking_obj = self.env['stock.picking']
        purchase_info = {}
        invoice_data = {
            'type': 'distributor',
            'sale_order_id': self.id,
            'order_line': [],
        }
        for sale_line in self.order_line:
            invoice_data['order_line'].append((0, 0, {
                'product_id': sale_line.product_id.id,
                'platform_price': sale_line.product_id.platform_price,
                'product_uom_qty': sale_line.product_uom_qty,
                'product_uom': sale_line.product_uom.id,
            }))
            platform_pro_merchant = sale_line.sudo().product_id.product_tmpl_id.merchant_id
            supplier_id = platform_pro_merchant.partner_id.id
            if purchase_info.has_key(supplier_id):
                purchase_info[supplier_id]['order_line'].append((0, 0, {
                    'product_id': sale_line.product_id.id,
                    'name': sale_line.product_id.name,
                    'price_unit': sale_line.product_id.supplier_price,
                    'product_qty': sale_line.product_uom_qty,
                    'product_uom': sale_line.product_uom.id,
                    'date_planned': datetime.datetime.now(),
                }))
            else:
                purchase_info[supplier_id] = {
                    'sale_order_id': self.id,
                    'merchant_id': platform_pro_merchant.id,
                    'partner_id': supplier_id,
                    'state': 'draft',
                    'platform_purchase_state': 'send',
                    'currency_id': self.currency_id.id,
                    'date_order': datetime.datetime.now(),
                    'date_planned': datetime.datetime.now(),
                    'order_line': [(0, 0, {
                        'product_id': sale_line.product_id.id,
                        'name': sale_line.product_id.name,
                        'price_unit': sale_line.product_id.supplier_price,
                        'taxes_id': [(6, False, [])],
                        'product_qty': sale_line.product_uom_qty,
                        'product_uom': sale_line.product_uom.id,
                        'date_planned': datetime.datetime.now(),
                    })]
                }
        invoice = self.env['invoice'].create(invoice_data)
        for (supplier_id, val) in purchase_info.items():
            purchase_order = purchase_obj.create(val)
            val = {
                'type': 'supplier',
                'merchant_id': purchase_order.merchant_id.id,
                'purchase_order_id': purchase_order.id,
                'order_line': [],
            }
            for line in purchase_order.order_line:
                val['order_line'].append((0, 0, {
                    'product_id': line.product_id.id,
                    'platform_price': line.product_id.supplier_price,
                    'product_uom_qty': line.product_qty,
                    'product_uom': line.product_uom.id,
                    'freight': line.freight,
                }))
            supplier_invoice = self.env['invoice'].sudo().create(val)
        return
