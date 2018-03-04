# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.osv import osv
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError

class FbaReplenish(models.Model):
    _name = 'fba.replenish'
    _order = 'id desc'

    name = fields.Char(string=u'单号')

    note = fields.Text(u'备注')

    delivery_count = fields.Integer(compute='_compute_delivery_count')
    distributor_invoice_count = fields.Integer(compute='_compute_invoice_count')
    supplier_invoice_count = fields.Integer(compute='_compute_invoice_count')

    freight = fields.Float(string=u'运费(元)', digits=(16,2))
    distributor_amount = fields.Float(compute='_compute_amount', string=u'金额(元)')
    supplier_amount = fields.Float(compute='_compute_amount', string=u'金额(元)')

    hide_distributor_info = fields.Boolean(compute='_compute_hide_info')
    hide_supplier_info = fields.Boolean(compute='_compute_hide_info')
    own_data = fields.Boolean(search='_search_own_data', store=False)

    country_id = fields.Many2one('amazon.country', string=u'发往国家', required=True)
    distributor = fields.Many2one('res.users', string=u'经销商', required=True,
                                  default=lambda self: self.env.user.merchant_id or self.env.user)
    supplier = fields.Many2one('res.users', string=u'供应商', required=False)
    logistics_company_id = fields.Many2one('logistics.company', string=u'物流公司')

    order_line = fields.One2many('fba.replenish.line', 'order_id', string=u'订单明细')
    purchase_orders = fields.One2many('purchase.order', 'fba_replenish_id')
    picking_ids = fields.One2many('stock.picking', 'fba_replenish_id')
    invoices = fields.One2many('invoice', 'fba_replenish_id')
    distributor_invoices = fields.One2many('invoice', 'fba_replenish_id', domain=[('type', '=', 'distributor')])
    supplier_invoices = fields.One2many('invoice', 'fba_replenish_id', domain=[('type', '=', 'supplier')])

    method = fields.Selection([
        ('sea', u'海运'),
        ('air', u'空运'),
        ('currier', u'特快'),
        ('post', u'平邮')], string=u'运输方式', required=True)
    type = fields.Selection([
        ('supplier_delivery', u'供应商代发'),
        ('other_delivery', u'第三方机构发货')
    ], string=u'发货方式', required=True)
    state = fields.Selection([
        ('draft', u'新建'),
        ('wait_supplier_confirm', u'待供应商确认'),
        ('wait_platform_confirm', u'待平台确认'),
        ('wait_distributor_confirm', u'待经销商确认'),
        ('wait_delivery', u'待发货'),
        ('done', u'完成'),
        ('cancel', u'取消')], string=u'状态', default='draft')

    @api.multi
    def _compute_invoice_count(self):
        for record in self:
            record.distributor_invoice_count = len(record.distributor_invoices)
            record.supplier_invoice_count = len(record.supplier_invoices)

    @api.multi
    def view_distributor_invoice(self):
        self.ensure_one()
        return {
            'name': u'发票',
            'type': 'ir.actions.act_window',
            'res_model': 'invoice',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [
                (self.env.ref('b2b_platform.invoice_tree').id, 'tree'),
                (self.env.ref('b2b_platform.invoice_form').id, 'form')],
            'domain': [('id', 'in', self.distributor_invoices.ids)],
            'target': 'current',
        }

    @api.multi
    def view_supplier_invoice(self):
        self.ensure_one()
        return {
            'name': u'发票',
            'type': 'ir.actions.act_window',
            'res_model': 'invoice',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [
                (self.env.ref('b2b_platform.invoice_tree').id, 'tree'),
                (self.env.ref('b2b_platform.invoice_form').id, 'form')],
            'domain': [('id', 'in', self.supplier_invoices.ids)],
            'target': 'current',
        }

    @api.model
    def _search_own_data(self, operation, value):
        merchant = self.env.user.merchant_id or self.env.user
        obj = self.env['fba.replenish']
        if self.user_has_groups('b2b_platform.b2b_shop_operator'):
            fbas = obj.search(['|', ('distributor', '=', merchant.id), ('supplier', '=', merchant.id)])
            return [('id', 'in', fbas.ids)]
        elif self.user_has_groups('b2b_platform.b2b_seller'):
            fbas = obj.search(['|', ('distributor', '=', merchant.id), ('supplier', '=', merchant.id)])
            return [('id', 'in', fbas.ids)]

    @api.multi
    def _compute_hide_info(self):
        for record in self:
            if record.state == 'draft':
                record.hide_distributor_info = False
                record.hide_supplier_info = True
            else:
                pass

    @api.multi
    def _compute_delivery_count(self):
        for record in self:
            record.delivery_count = len(record.picking_ids)

    @api.multi
    def view_delivery(self):
        self.ensure_one()
        return {
            'name': u'发货单',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [(self.env.ref('amazon_api.stock_picking_tree').id, 'tree'),
                      (self.env.ref('amazon_api.b2b_stock_picking_form').id, 'form')],
            'domain': [('fba_replenish_id', '=', self.id)],
            'target': 'current',
        }

    @api.multi
    def _compute_amount(self):
        for record in self:
            distributor_amount = 0
            supplier_amount = 0
            for line in record.order_line:
                distributor_amount += line.platform_price * line.need_qty
                supplier_amount += line.supplier_price * line.available_qty
            record.distributor_amount = distributor_amount
            record.supplier_amount = supplier_amount

    @api.multi
    def send_request(self):
        '''补货申请'''
        self.ensure_one()
        self.state = 'wait_supplier_confirm'

    @api.multi
    def supplier_confirm(self):
        '''供应商确认'''
        self.ensure_one()
        if self.type == 'supplier_delivery':
            self.state = 'wait_distributor_confirm'
        elif self.type == 'other_delivery':
            self.state == 'wait_platform_confirm'

    @api.multi
    def platform_confirm(self):
        '''平台核算运费'''
        self.ensure_one()
        self.state = 'wait_distributor_confirm'

    # @api.multi
    # def distributor_confirm(self):
    #     '''经销商确认'''
    #     self.ensure_one()
    #     self.state = 'purchase'
    #     cny = self.env['res.currency'].search([('name', '=', 'CNY')], limit=1)
    #     val = {
    #         'delivery_mode': 'FBA',
    #         'partner_id': self.supplier.partner_id.id,
    #         'fba_replenish_id': self.id,
    #         'state': 'draft',
    #         'origin': self.name,
    #         'currency_id': cny.id,
    #         'date_order': datetime.now(),
    #         'date_planned': datetime.now(),
    #         'order_line': [],
    #     }
    #     for line in self.order_line:
    #         val['order_line'].append((0, 0, {
    #             'product_id': line.product_id.id,
    #             'name': line.product_id.name,
    #             'price_unit': line.supplier_price,
    #             'taxes_id': [(6, False, [])],
    #             'product_qty': line.available_qty,
    #             'product_uom': line.product_uom.id,
    #             'date_planned': datetime.now(),
    #             'freight': 0,
    #             'fba_replenish_line_id': line.id,
    #         }))
    #     purchase = self.env['purchase.order'].create(val)
    #     return self.view_purchase_order()


    @api.multi
    def distributor_confirm(self):
        '''经销商确认'''
        self.ensure_one()
        self.state = 'wait_delivery'
        stock_picking_obj = self.env['stock.picking']
        loc_obj = self.env['stock.location']
        merchant = self.env.user.merchant_id or self.env.user
        supplier = self.supplier.partner_id
        location = loc_obj.search([
            ('partner_id', '=', supplier.id),
            ('location_id', '=', self.env.ref('b2b_platform.third_warehouse').id)], limit=1)
        if not location:
            location = loc_obj.search([
                ('partner_id', '=', supplier.id),
                ('location_id', '=', self.env.ref('b2b_platform.supplier_stock').id)], limit=1)
        if not location:
            raise UserError(u'Not found supplier b2b location!')
        location_dest_id = self.env.ref('stock.stock_location_customers').id
        val = {
            'partner_id': supplier.id,
            'merchant_id': merchant.id,
            'location_id': location.id,
            'location_dest_id': location_dest_id,
            'picking_type_id': 4,
            'b2b_type': 'outgoing',
            'origin_type': 'fba_delivery',
            'origin': self.name,
            'fba_replenish_id': self.id,
            'pack_operation_product_ids': [],
        }
        for line in self.order_line:
            val['pack_operation_product_ids'].append((0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.available_qty,
                'qty_done': line.available_qty,
                'product_uom_id': line.product_uom.id,
                'location_id': location.id,
                'location_dest_id': location_dest_id,
                'fba_replenish_line_id': line.id,
            }))
        delivery = stock_picking_obj.create(val)
        #生成经销商发票
        invoice_val = {
            'fba_freight': self.freight,
            'type': 'distributor',
            'fba_replenish_id': self.id,
            'origin': self.name,
            'order_line': [],
        }
        for line in self.order_line:
            invoice_val['order_line'].append((0, 0, {
                'product_id': line.product_id.id,
                'platform_price': line.platform_price,
                'product_uom_qty': line.available_qty,
                'product_uom': line.product_uom.id,
                'freight': 0,
            }))
        invoice = self.env['invoice'].create(invoice_val)
        invoice.invoice_confirm()

    @api.model
    def create(self, val):
        if not val.get('name'):
            val['name'] = self.env['ir.sequence'].next_by_code('fba.replenish.number') or '/'
        result = super(FbaReplenish, self).create(val)
        result.check_data()
        return result

    @api.multi
    def write(self, val):
        result = super(FbaReplenish, self).write(val)
        self.check_data()
        return result

    @api.multi
    def check_data(self):
        for record in self:
            suppliers = []
            for line in record.order_line:
                suppliers.append(line.supplier.id)
            suppliers = list(set(suppliers))
            if len(suppliers) > 1:
                raise UserError(u'只能选择一个供应商供应商不符')
            elif len(suppliers) == 1:
                pass
            else:
                raise UserError(u'不能建一个空的补货单！')



class FbaReplenishLine(models.Model):
    _name = 'fba.replenish.line'

    order_id = fields.Many2one('fba.replenish', ondelete='cascade')
    product_id = fields.Many2one('product.product', inverse='_change_supplier', domain=[('state', '=', 'platform_published')],
                                 string=u'产品')
    product_uom = fields.Many2one('product.uom', string=u'计量单位', related='product_id.uom_id', readonly=True)
    supplier = fields.Many2one('res.users', related='product_id.product_tmpl_id.merchant_id', string=u'供应商')

    need_qty = fields.Float(string=u'需求数量', digits=(16,3))
    available_qty = fields.Float(string=u'补货数量', digits=(16,3))
    platform_price = fields.Float(compute='_compute_price', store=True, readonly=True, string=u'采购单价(元)')
    supplier_price = fields.Float(compute='_compute_price', store=True, readonly=True, string=u'供货单价(元)')
    distributor_total = fields.Float(string=u'金额(元)', digits=(16, 2), compute='')
    supplier_total = fields.Float(string=u'金额(元)',digits=(16,2), compute='')

    state = fields.Selection([
        ('draft', u'新建'),
        ('wait_supplier_confirm', u'待供应商确认'),
        ('wait_platform_confirm', u'待平台确认'),
        ('wait_distributor_confirm', u'待经销商确认'),
        ('purchase', u'已转采购'),
        ('done', u'完成'),
        ('cancel', u'取消')], related='order_id.state', string=u'状态')

    state = fields.Selection([
        ('draft', u'新建'),
        ('wait_supplier_confirm', u'待供应商确认'),
        ('wait_platform_confirm', u'待平台确认'),
        ('wait_distributor_confirm', u'待经销商确认'),
        ('done', u'完成'),
        ('cancel', u'取消'),
    ], related='order_id.state', default='draft', store=False, string=u'状态')

    @api.multi
    def _change_supplier(self):
        print '_change_supplier'
        for record in self:
            print record.supplier
            record.order_id.supplier = record.supplier.id

    @api.depends('product_id')
    def _compute_price(self):
        for record in self:
            record.platform_price = record.product_id.platform_price
            record.supplier_price = record.product_id.supplier_price




