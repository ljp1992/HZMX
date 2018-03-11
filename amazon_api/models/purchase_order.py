# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import copy

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    origin = fields.Char(string=u'来源单据')

    freight = fields.Float(compute='_compute_freight', store=False, string=u'运费')

    b2b_delivery_count = fields.Integer(compute='_b2b_order_count')
    b2b_invoice_count = fields.Integer(compute='_b2b_order_count')

    b2b_total = fields.Float(compute='_compute_total', store=False, string=u'合计')
    fba_freight = fields.Float(string=u'FBA运费')

    own_data = fields.Boolean(search='_own_data_search', store=False)
    own_record = fields.Boolean(compute='_own_record')
    hide_delivery_button = fields.Boolean(compute='_hide_delivery_button')

    delivery_order_count = fields.Integer(compute='_delivery_order_count')

    sale_order_id = fields.Many2one('sale.order')
    replenish_order_id = fields.Many2one('replenish.order', string=u'补货单')
    fba_replenish_id = fields.Many2one('fba.replenish', string=u'FBA补货单')
    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user,
                                  string=u'商户')
    e_country_id = fields.Many2one('amazon.country', related='sale_order_id.country_id', string=u'发往国家')

    deliverys = fields.One2many('stock.picking', 'purchase_order_id')
    b2b_invoice_ids = fields.One2many('invoice', 'purchase_order_id', string=u'发票')

    b2b_state = fields.Selection([
        ('draft', u'待处理'),
        ('confirmed', u'待发货'),
        ('done', u'已发货'),
    ], default='draft', string=u'状态')
    origin_type = fields.Selection([
        ('FBA', u'FBA补货'),
        ('sale', u'客户订单'),
    ], default='sale', compute='_compute_origin_type', store=False, string=u'来源')

    @api.multi
    def _compute_origin_type(self):
        for record in self:
            if record.sale_order_id:
                record.origin_type = 'sale'
            elif record.fba_replenish_id:
                record.origin_type = 'FBA'

    @api.multi
    def compute_puchase_order_state(self):
        '''计算采购单状态'''
        for record in self:
            if record.deliverys:
                states = set([picking.b2b_state for picking in record.deliverys])
                if states == {'done'}:
                    record.b2b_state = 'done'
                else:
                    record.b2b_state = 'confirmed'
            else:
                record.b2b_state = 'draft'
            if record.sale_order_id:
                record.sale_order_id.compute_sale_order_state()
            if record.fba_replenish_id:
                record.fba_replenish_id.compute_fb2_replenish_state()

    @api.multi
    def confirm_purchase_ljp(self):
        '''确认采购单'''
        self.ensure_one()
        stock_picking_obj = self.env['stock.picking']
        loc_obj = self.env['stock.location']
        pro_obj = self.env['product.product']
        merchant = self.env['res.users'].search([('partner_id', '=', self.partner_id.id)], limit=1)
        if not merchant:
            raise UserError(u'没有找到供应商账号！')
        third_location = loc_obj.return_merchant_third_location(merchant)
        supplier_location = loc_obj.return_merchant_supplier_location(merchant)
        if not supplier_location:
            raise UserError(u'Not found supplier b2b location!')
        location_dest_id = self.env.ref('stock.stock_location_customers').id
        val = {
            'partner_id': merchant.partner_id.id,
            'location_id': supplier_location.id,
            'location_dest_id': location_dest_id,
            'picking_type_id': 4,
            'b2b_type': 'outgoing',
            'origin': self.name,
            'purchase_order_id': self.id or False,
            'pack_operation_product_ids': [],
        }
        for line in self.order_line:
            #自动分配从哪个仓库发货
            line_val = {
                'product_id': line.product_id.id,
                'product_qty': line.product_qty,
                'qty_done': line.product_qty,
                'product_uom_id': line.product_uom.id,
                'location_dest_id': location_dest_id,
                'b2b_purchase_line_id': line.id,
            }
            supplier_loc_inventory = pro_obj.get_loc_pro_usable_inventory(line.product_id, supplier_location)
            if third_location:
                third_loc_inventory = pro_obj.get_loc_pro_usable_inventory(line.product_id, third_location)
                if third_loc_inventory >= line.product_qty:
                    line_val['location_id'] = third_location.id
                    val['pack_operation_product_ids'].append((0, 0, line_val))
                else:
                    if third_loc_inventory > 0:
                        line_val_copy = copy.deepcopy(line_val)
                        line_val.update({
                            'location_id': third_location.id,
                            'product_qty': third_loc_inventory,
                            'qty_done': third_loc_inventory,
                        })
                        if supplier_loc_inventory >= line.product_qty - third_loc_inventory:
                            line_val_copy.update({
                                'location_id': supplier_location.id,
                                'product_qty': line.product_qty - third_loc_inventory,
                                'qty_done': line.product_qty - third_loc_inventory,
                            })
                        else:
                            raise UserError(u'库存不足！')
                        val['pack_operation_product_ids'].append((0, 0, line_val))
                        val['pack_operation_product_ids'].append((0, 0, line_val_copy))
                    else:
                        if line.product_qty > supplier_loc_inventory:
                            raise UserError(u'产品%s库存不足！' % (line.product_id.name))
                        else:
                            line_val['location_id'] = supplier_location.id
                            val['pack_operation_product_ids'].append((0, 0, line_val))
            else:
                if line.product_qty > supplier_loc_inventory:
                    raise UserError(u'产品%s库存不足！' % (line.product_id.name))
                else:
                    line_val['location_id'] = supplier_location.id
                    val['pack_operation_product_ids'].append((0, 0, line_val))
        delivery = stock_picking_obj.create(val)
        delivery.create_delivery_info()
        self.compute_puchase_order_state()
        return {
            'name': u'发货单',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [(self.env.ref('amazon_api.stock_picking_tree').id, 'tree'),
                      (self.env.ref('amazon_api.b2b_stock_picking_form').id, 'form')],
            'domain': [('id', '=', delivery.id)],
            'target': 'current',
        }

    @api.multi
    def unlink(self):
        for record in self:
            record.state = 'cancel'
        return super(PurchaseOrder, self).unlink()

    @api.multi
    def _own_record(self):
        merchant = self.env.user.merchant_id or self.env.user
        for record in self:
            if record.partner_id == merchant.partner_id:
                record.own_record = True
            else:
                record.own_record = False

    def _hide_delivery_button(self):
        merchant = self.env.user.merchant_id or self.env.user
        for record in self:
            if record.merchant_id == merchant:
                record.hide_delivery_button = False
            else:
                record.hide_delivery_button = True
            if record.platform_purchase_state != 'send':
                record.hide_delivery_button = True

    @api.multi
    def _compute_total(self):
        for record in self:
            total = 0
            for line in record.order_line:
                total += line.b2b_total
            record.b2b_total = total + record.fba_freight

    def _compute_freight(self):
        for record in self:
            freight = 0
            for line in record.order_line:
                freight += line.freight
            record.freight = freight

    def _b2b_order_count(self):
        for record in self:
            record.b2b_delivery_count = len(record.deliverys)
            record.b2b_invoice_count = len(record.b2b_invoice_ids)

    def view_invoice(self):
        return {
            'name': u'供应商发票',
            'type': 'ir.actions.act_window',
            'res_model': 'invoice',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [
                (self.env.ref('amazon_api.invoice_tree').id, 'tree'),
                (self.env.ref('amazon_api.invoice_form').id, 'form')],
            'domain': [('id', 'in', self.b2b_invoice_ids.ids)],
            'target': 'current',
        }

    @api.model
    def _own_data_search(self, operator, value):
        merchant = self.env.user.merchant_id or self.env.user
        if self.user_has_groups('b2b_platform.b2b_shop_operator') or self.user_has_groups('b2b_platform.b2b_seller'):
            return [('partner_id', '=', merchant.partner_id.id)]

    @api.multi
    def view_delivery_order(self):
        return {
            'name': u'发货单',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [
                (self.env.ref('amazon_api.stock_picking_tree').id, 'tree'),
                (self.env.ref('amazon_api.b2b_stock_picking_form').id, 'form')],
            'domain': [('id', 'in', self.deliverys.ids)],
            'target': 'current',
        }



    @api.multi
    def _delivery_order_count(self):
        for purchase in self:
            purchase.delivery_order_count = len(purchase.deliverys)

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
        if context.get('view_own_purchase'):
            merchant_id = self.env.user.merchant_id or self.env.user
            if self.user_has_groups('b2b_platform.b2b_shop_operator'):
                args += [('partner_id', '=', merchant_id.partner_id.id)]
            elif self.user_has_groups('b2b_platform.b2b_seller'):
                args += [('partner_id', '=', merchant_id.partner_id.id)]
            elif self.user_has_groups('b2b_platform.b2b_manager'):
                pass
            else:
                pass
        return super(PurchaseOrder, self).search(args, offset, limit, order, count=count)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    freight = fields.Float(store=True, string=u'运费')
    b2b_total = fields.Float(compute='_compute_total', store=False, string=u'小计')

    b2b_sale_line_id = fields.Many2one('sale.order.line')
    fba_replenish_line_id = fields.Many2one('fba.replenish.line')
    replenish_line_id = fields.Many2one('replenish.order.line')

    def _compute_total(self):
        for record in self:
            record.b2b_total = record.price_unit * record.product_qty + record.freight


