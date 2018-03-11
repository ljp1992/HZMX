# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import copy

class StockImmediateTransfer(models.TransientModel):
    _inherit = "stock.immediate.transfer"

    @api.multi
    def process(self):
        '''移动'''
        context = self.env.context or {}
        pickings = self.env['stock.picking'].search([('id', 'in', context.get('active_ids'))])
        if pickings:
            result = super(StockImmediateTransfer, self).process()
            pickings.check_inventory_legal()
            #创建发票
            pickings.create_supplier_invoice_platform_purchase()
            pickings.create_freight_invoice()
            pickings.create_supplier_invoice_fba_replenish()
            #修改状态
            pickings.write({'b2b_state': 'done'})
            pickings.modify_related_order_state()
            return result

    # @api.multi
    # def process(self):
    #     '''移动'''
    #     result = super(StockImmediateTransfer, self).process()
    #     loc_obj = self.env['stock.location']
    #     merchant = self.env.user.merchant_id or self.env.user
    #     context = self.env.context or {}
    #     pickings = self.env['stock.picking'].search([('id', 'in', context.get('active_ids'))])
    #     if pickings:
    #         pickings.write({'b2b_state': 'done'})
    #         for picking in pickings:
    #             sale_order = picking.sale_order_id
    #             if sale_order:
    #                 sale_order_done = True
    #                 if sale_order.deliverys.filtered(lambda r: r.b2b_state == 'draft'):
    #                     sale_order_done = False
    #                 if sale_order_done:
    #                     sale_order.b2b_state = 'delivered'
    #             # invoice
    #             invoice_obj = self.env['invoice']
    #             if picking.origin_type == 'own_delivery': #自有产品平台发货，生成运费账单
    #                 invoice_val = {
    #                     'picking_id': picking.id,
    #                     'sale_order_id': sale_order.id,
    #                     'merchant_id': merchant.id,
    #                     'origin': sale_order.name,
    #                     'type': 'distributor',
    #                     'state': 'paid',
    #                     'order_line': []
    #                 }
    #                 create_invoice = False
    #                 for line in picking.pack_operation_product_ids:
    #                     invoice_val['order_line'].append((0, 0, {
    #                         'product_id': line.product_id.id,
    #                         'product_uom_qty': line.qty_done,
    #                         'product_uom': line.product_uom_id.id,
    #                         'platform_price': 0,
    #                         'freight': line.b2b_sale_line_id.supplier_freight,
    #                         'operation_line_id': line.id,
    #                     }))
    #                     if line.platform_location:
    #                         create_invoice = True
    #                 if create_invoice:
    #                     invoice = invoice_obj.create(invoice_val)
    #                     invoice.invoice_confirm()
    #             elif picking.origin_type == 'agent_delivery': #平台采购生成发票（供应商库位发货的发票，第三方仓库发货的发票）
    #                 purchase_order = picking.purchase_order_id
    #                 if purchase_order:
    #                     purchase_order._compute_b2b_state()
    #                 third_loc = loc_obj.search([
    #                     ('partner_id', '=', merchant.partner_id.id),
    #                     ('location_id', '=', self.env.ref('b2b_platform.third_warehouse').id)], limit=1)
    #                 supplier_loc = loc_obj.search([
    #                         ('partner_id', '=', merchant.partner_id.id),
    #                         ('location_id', '=', self.env.ref('b2b_platform.supplier_stock').id)], limit=1)
    #                 third_loc_invoice = {
    #                     'picking_id': picking.id,
    #                     'sale_order_id': sale_order.id,
    #                     'purchase_order_id': picking.purchase_order_id.id,
    #                     'merchant_id': merchant.id,
    #                     'type': 'supplier',
    #                     'detail_type': 'supplier_third_stock',
    #                     'origin': picking.purchase_order_id.name,
    #                     'state': 'draft',
    #                     'order_line': []
    #                 }
    #                 supplier_loc_invoice = copy.deepcopy(third_loc_invoice)
    #                 supplier_loc_invoice['detail_type'] = 'supplier_own_stock'
    #                 for line in picking.pack_operation_product_ids:
    #                     if line.location_id == supplier_loc:
    #                         supplier_loc_invoice['order_line'].append((0, 0, {
    #                             'product_id': line.product_id.id,
    #                             'product_uom_qty': line.qty_done,
    #                             'product_uom': line.product_uom_id.id,
    #                             'platform_price': line.product_id.supplier_price,
    #                             'freight': line.b2b_sale_line_id.supplier_freight,
    #                             'operation_line_id': line.id,
    #                         }))
    #                     elif line.location_id == third_loc:
    #                         third_loc_invoice['order_line'].append((0, 0, {
    #                             'product_id': line.product_id.id,
    #                             'product_uom_qty': line.qty_done,
    #                             'product_uom': line.product_uom_id.id,
    #                             'platform_price': line.product_id.supplier_price,
    #                             'freight': 0,
    #                             'operation_line_id': line.id,
    #                         }))
    #                 if supplier_loc_invoice.get('order_line'):
    #                     invoice = invoice_obj.create(supplier_loc_invoice)
    #                 if third_loc_invoice.get('order_line'):
    #                     invoice = invoice_obj.create(third_loc_invoice)
    #             elif picking.origin_type == 'fba_delivery': #fba 补发货
    #                 picking.purchase_order_id.b2b_state = 'done'
    #                 picking.fba_replenish_id.state = 'done'
    #                 third_loc = loc_obj.search([
    #                     ('partner_id', '=', merchant.partner_id.id),
    #                     ('location_id', '=', self.env.ref('b2b_platform.third_warehouse').id)], limit=1)
    #                 supplier_loc = loc_obj.search([
    #                     ('partner_id', '=', merchant.partner_id.id),
    #                     ('location_id', '=', self.env.ref('b2b_platform.supplier_stock').id)], limit=1)
    #                 third_loc_invoice = {
    #                     'picking_id': picking.id,
    #                     'fba_freight': picking.fba_replenish_id.freight,
    #                     'fba_replenish_id': picking.fba_replenish_id.id,
    #                     'purchase_order_id': picking.purchase_order_id.id,
    #                     'merchant_id': merchant.id,
    #                     'type': 'supplier',
    #                     'detail_type': 'supplier_fba_third_stock',
    #                     'origin': picking.fba_replenish_id.name,
    #                     'state': 'draft',
    #                     'order_line': []
    #                 }
    #                 supplier_loc_invoice = copy.deepcopy(third_loc_invoice)
    #                 supplier_loc_invoice['detail_type'] = 'supplier_fba_own_stock'
    #                 for line in picking.pack_operation_product_ids:
    #                     if line.location_id == supplier_loc:
    #                         supplier_loc_invoice['order_line'].append((0, 0, {
    #                             'product_id': line.product_id.id,
    #                             'product_uom_qty': line.qty_done,
    #                             'product_uom': line.product_uom_id.id,
    #                             'platform_price': line.product_id.supplier_price,
    #                             'freight': 0,
    #                             'operation_line_id': line.id,
    #                         }))
    #                     elif line.location_id == third_loc:
    #                         third_loc_invoice['order_line'].append((0, 0, {
    #                             'product_id': line.product_id.id,
    #                             'product_uom_qty': line.qty_done,
    #                             'product_uom': line.product_uom_id.id,
    #                             'platform_price': 0,
    #                             'freight': 0,
    #                             'operation_line_id': line.id,
    #                         }))
    #                 if supplier_loc_invoice.get('order_line'):
    #                     invoice = invoice_obj.create(supplier_loc_invoice)
    #                 if third_loc_invoice.get('order_line'):
    #                     invoice = invoice_obj.create(third_loc_invoice)
    #     return result