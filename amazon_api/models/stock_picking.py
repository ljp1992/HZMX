# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime, copy
from odoo.addons.amazon_api.amazon_api.mws import Feeds

class StockPicking(models.Model):
    _inherit = "stock.picking"
    _order = 'id desc'

    province = fields.Char(string=u'州／省')
    city = fields.Char(string=u'市')
    street = fields.Char(string=u'街道')
    postal_code = fields.Char(string=u'邮编')
    phone = fields.Char(string=u'电话')
    e_mail = fields.Char(string=u'邮箱')
    shippment_number = fields.Char(string=u'物流单号')

    receiver_info = fields.Text(string=u'收件信息')

    hide_delivery_button = fields.Boolean(compute='_hide_delivery_button')
    own_record = fields.Boolean(compute='_own_record')
    own_picking = fields.Boolean(search='_compute_own_picking', store=False)

    delivery_date = fields.Datetime(string=u'发货时间')

    # own_data = fields.Boolean(search='_own_data_search', store=False)
    b2b_log_count = fields.Integer(compute='_b2b_log_count')
    b2b_invoice_count = fields.Integer(compute='_compute_invoice_count', store=False)

    location_id = fields.Many2one('stock.location', default=lambda self: self._b2b_location_id())
    location_dest_id = fields.Many2one('stock.location', default=lambda self: self._b2b_location_dest_id())
    partner_id = fields.Many2one(default=lambda self: self.env.user.partner_id)
    merchant_id = fields.Many2one('res.users', string=u'商户')
    country_id = fields.Many2one('amazon.country', string=u'国家')
    logistics_company_id = fields.Many2one('logistics.company', string=u'物流公司')
    sale_order_id = fields.Many2one('sale.order')
    purchase_order_id = fields.Many2one('purchase.order')
    fba_replenish_id = fields.Many2one('fba.replenish')
    replenish_order_id = fields.Many2one('replenish.order', string=u'补货单')

    invoices = fields.One2many('invoice', 'picking_id')

    delivery_info_upload_state = fields.Selection([
        ('no_upload', u'未上传'),
        ('uploading', u'正在上传'),
        ('done', u'上传成功'),
        ('failed', u'上传失败'),
    ], default='no_upload', string=u'发货信息上传状态')
    b2b_type = fields.Selection([
        ('incoming', u'入库'),
        ('outgoing', u'出库'),
        ('internal', u'调拨')
    ], string=u'类型')
    b2b_state = fields.Selection([
        ('draft', u'新建'),
        ('done', u'完成'),
    ], default='draft', string=u'状态')
    origin_type = fields.Selection([
        ('own_delivery', u'自有发货'),
        ('agent_delivery', u'代发货'),
        ('fba_delivery', u'FBA补货'),
    ], compute='_compute_origin_type', store=False, string=u'类型')

    @api.multi
    def view_invoice(self):
        self.ensure_one()
        return {
            'name': u'发票',
            'type': 'ir.actions.act_window',
            'res_model': 'invoice',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [
                (self.env.ref('amazon_api.invoice_tree').id, 'tree'),
                (self.env.ref('amazon_api.invoice_form').id, 'form')],
            'domain': [('picking_id', '=', self.id)],
            'target': 'current',
        }

    @api.multi
    def _compute_invoice_count(self):
        for picking in self:
            picking.b2b_invoice_count = len(picking.invoices)

    @api.multi
    def modify_related_order_state(self):
        '''修改相关单据状态'''
        for record in self:
            if record.sale_order_id:
                record.sale_order_id.compute_sale_order_state()
            elif record.purchase_order_id:
                record.purchase_order_id.compute_puchase_order_state()

    @api.multi
    def check_inventory_legal(self):
        '''检查发货后的库存数量是否小于0'''
        pro_obj = self.env['product.product']
        for picking in self:
            for line in picking.pack_operation_product_ids:
                inventory = pro_obj.get_product_actual_inventory(line.product_id, line.location_id)
                if inventory < 0:
                    raise UserError(u'产品%s库存不足!' % (line.product_id.name))

    @api.multi
    def create_freight_invoice(self):
        '''创建发票（自有发货）'''
        loc_obj = self.env['stock.location']
        invoice_obj = self.env['invoice']
        for picking in self:
            if picking.sale_order_id:
                merchant = self.env['res.users'].search([('partner_id', '=', picking.partner_id.id)], limit=1)
                if not merchant:
                    raise UserError(u'Not found merchant!')
                third_loc = loc_obj.return_merchant_third_location(merchant)
                third_loc_invoice = {
                    'merchant_id': merchant.id,
                    'picking_id': picking.id,
                    'origin': picking.name,
                    'type': 'distributor_own_delivery',
                    'order_line': []
                }
                for line in picking.pack_operation_product_ids:
                    if line.location_id == third_loc:
                        third_loc_invoice['order_line'].append((0, 0, {
                            'product_id': line.product_id.id,
                            'product_uom_qty': line.qty_done,
                            'product_uom': line.product_uom_id.id,
                            'platform_price': 0,
                            'freight': line.b2b_sale_line_id and line.b2b_sale_line_id.supplier_freight or 0,
                            'operation_line_id': line.id,
                        }))
                if third_loc_invoice.get('order_line'):
                    invoice = invoice_obj.create(third_loc_invoice)
                    invoice.invoice_confirm()

    @api.multi
    def create_supplier_invoice_platform_purchase(self):
        '''创建供应商发票（平台采购）'''
        loc_obj = self.env['stock.location']
        invoice_obj = self.env['invoice']
        for picking in self:
            if picking.purchase_order_id and picking.purchase_order_id.sale_order_id:
                merchant = self.env['res.users'].search([('partner_id', '=', picking.partner_id.id)], limit=1)
                if not merchant:
                    raise UserError(u'Not found merchant!')
                third_loc = loc_obj.return_merchant_third_location(merchant)
                supplier_loc = loc_obj.return_merchant_supplier_location(merchant)
                val = {
                    'merchant_id': merchant.id,
                    'picking_id': picking.id,
                    'origin': picking.name,
                    'order_line': []
                }
                supplier_loc_invoice = copy.deepcopy(val)
                supplier_loc_invoice['type'] = 'supplier_own_stock'
                third_loc_invoice = copy.deepcopy(val)
                third_loc_invoice['type'] = 'supplier_third_stock'
                for line in picking.pack_operation_product_ids:
                    if line.location_id == supplier_loc:
                        supplier_loc_invoice['order_line'].append((0, 0, {
                            'product_id': line.product_id.id,
                            'product_uom_qty': line.qty_done,
                            'product_uom': line.product_uom_id.id,
                            'platform_price': line.b2b_purchase_line_id and line.b2b_purchase_line_id.price_unit or 0,
                            'freight': line.b2b_purchase_line_id.freight or 0,
                            'operation_line_id': line.id,
                        }))
                    elif line.location_id == third_loc:
                        third_loc_invoice['order_line'].append((0, 0, {
                            'product_id': line.product_id.id,
                            'product_uom_qty': line.qty_done,
                            'product_uom': line.product_uom_id.id,
                            'platform_price': line.b2b_purchase_line_id and line.b2b_purchase_line_id.price_unit or 0,
                            'freight': 0,
                            'operation_line_id': line.id,
                        }))
                if supplier_loc_invoice.get('order_line'):
                    invoice_obj.create(supplier_loc_invoice)
                if third_loc_invoice.get('order_line'):
                    invoice_obj.create(third_loc_invoice)

    @api.multi
    def create_supplier_invoice_fba_replenish(self):
        '''创建供应商发票（FBA补货）'''
        loc_obj = self.env['stock.location']
        invoice_obj = self.env['invoice']
        for picking in self:
            fba_replenish = picking.purchase_order_id and picking.purchase_order_id.fba_replenish_id
            if fba_replenish:
                merchant = self.env['res.users'].search([('partner_id', '=', picking.partner_id.id)], limit=1)
                if not merchant:
                    raise UserError(u'Not found merchant!')
                third_loc = loc_obj.return_merchant_third_location(merchant)
                supplier_loc = loc_obj.return_merchant_supplier_location(merchant)
                if fba_replenish.type == 'supplier_delivery':
                    fba_freight = fba_replenish.freight or 0
                elif fba_replenish.type == 'other_delivery':
                    fba_freight = 0
                val = {
                    'merchant_id': merchant.id,
                    'picking_id': picking.id,
                    'origin': picking.name,
                    'fba_freight': fba_freight,
                    'order_line': []
                }
                supplier_loc_invoice = copy.deepcopy(val)
                supplier_loc_invoice['type'] = 'supplier_fba_own_stock'
                third_loc_invoice = copy.deepcopy(val)
                third_loc_invoice['type'] = 'supplier_fba_third_stock'
                for line in picking.pack_operation_product_ids:
                    if line.location_id == supplier_loc:
                        supplier_loc_invoice['order_line'].append((0, 0, {
                            'product_id': line.product_id.id,
                            'product_uom_qty': line.qty_done,
                            'product_uom': line.product_uom_id.id,
                            'platform_price': line.b2b_purchase_line_id and line.b2b_purchase_line_id.price_unit or 0,
                            'freight': 0,
                            'operation_line_id': line.id,
                        }))
                    elif line.location_id == third_loc:
                        third_loc_invoice['order_line'].append((0, 0, {
                            'product_id': line.product_id.id,
                            'product_uom_qty': line.qty_done,
                            'product_uom': line.product_uom_id.id,
                            'platform_price': line.b2b_purchase_line_id and line.b2b_purchase_line_id.price_unit or 0,
                            'freight': 0,
                            'operation_line_id': line.id,
                        }))
                if supplier_loc_invoice.get('order_line'):
                    invoice_obj.create(supplier_loc_invoice)
                if third_loc_invoice.get('order_line'):
                    invoice_obj.create(third_loc_invoice)

    @api.multi
    def _compute_origin_type(self):
        for record in self:
            if record.sale_order_id:
                record.origin_type = 'own_delivery'
            elif record.purchase_order_id:
                if record.purchase_order_id.sale_order_id:
                    record.origin_type = 'agent_delivery'
                elif record.purchase_order_id.fba_replenish_id:
                    record.origin_type = 'fba_delivery'

    @api.model
    def _compute_own_picking(self, operation, value):
        merchant = self.env.user.merchant_id or self.env.user
        if self.user_has_groups('b2b_platform.b2b_shop_operator') or self.user_has_groups('b2b_platform.b2b_seller'):
            return [('partner_id', '=', merchant.partner_id.id)]


    @api.model
    def _b2b_location_id(self):
        merchant = self.env.user.merchant_id or self.env.user
        supplier_loc = self.env.ref('b2b_platform.supplier_stock').id
        loc = self.env['stock.location'].search([
            ('partner_id', '=', merchant.partner_id.id),
            ('location_id', '=', supplier_loc)])
        if loc:
            return loc

    @api.model
    def _b2b_location_dest_id(self):
        merchant = self.env.user.merchant_id or self.env.user
        third_warehouse = self.env.ref('b2b_platform.third_warehouse').id
        loc = self.env['stock.location'].search([
            ('partner_id', '=', merchant.partner_id.id),
            ('location_id', '=', third_warehouse)])
        if loc:
            return loc

    @api.multi
    def _b2b_log_count(self):
        for record in self:
            logs = self.env['submission.history'].search([
                ('model', '=', 'stock.picking'),
                ('record_id', '=', record.id)])
            record.b2b_log_count = len(logs)

    @api.multi
    def view_submission_history(self):
        self.ensure_one()
        return {
            'name': u'上传日志',
            'type': 'ir.actions.act_window',
            'res_model': 'submission.history',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [
                (self.env.ref('amazon_api.submission_history_tree').id, 'tree'),
                (self.env.ref('amazon_api.submission_history_form').id, 'form')],
            'domain': [('model', '=', 'stock.picking'), ('record_id', '=', self.id)],
            'target': 'current',
        }

    @api.onchange('location_id', 'location_dest_id')
    def b2b_onchange_location_id(self):
        for line in self.pack_operation_product_ids:
            line.location_id = self.location_id.id
            line.location_dest_id = self.location_dest_id.id

    def _hide_delivery_button(self):
        for record in self:
            if record.b2b_state == 'wait_delivery':
                record.hide_delivery_button = False
            else:
                record.hide_delivery_button = True

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100):
    #     args = args or []
    #     if name:
    #         args += [('name', operator, name)]
    #     result = self.search(args, limit=limit)
    #     return result.name_get()

    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     context = self.env.context or {}
    #     if context.get('view_own_picking'):
    #         if self.user_has_groups('b2b_platform.b2b_shop_operator'):
    #             args += [('partner_id', '=', self.env.user.partner_id.id)]
    #         elif self.user_has_groups('b2b_platform.b2b_seller'):
    #             self.env.user
    #             args += [('partner_id', '=', self.env.user.partner_id.id)]
    #         elif self.user_has_groups('b2b_platform.b2b_manager'):
    #             pass
    #         else:
    #             pass
    #     return super(StockPicking, self).search(args, offset, limit, order, count=count)

    # @api.model
    # def _own_data_search(self, operator, value):
    #     user = self.env.user
    #     if user.user_type == 'operator':
    #         return [('id', '=', 0)]
    #     elif user.user_type == 'merchant':
    #         return [('partner_id', '=', user.partner_id.id)]
    #     else:
    #         return []

    @api.multi
    def create_delivery_info(self):
        for record in self:
            sale_order = record.sale_order_id
            if sale_order:
                receiver_info = u"国家:%s\n州／省:%s\n市:%s\n街道:%s\n邮编:%s\n姓名:%s\n电话:%s\ne-mail:%s" % (
                    sale_order.country_id.name or '',
                    sale_order.province or '',
                    sale_order.city or '',
                    sale_order.street or '',
                    sale_order.postal_code or '',
                    sale_order.partner_id.name or '',
                    sale_order.phone or '',
                    sale_order.e_mail or '')
                record.receiver_info = receiver_info

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
    def b2b_do_new_transfer(self):
        '''移动'''
        self.ensure_one()
        if self.b2b_state == 'done':
            raise UserError(u'已经移动完成，无需再次操作！')
        return {
            'name': u'移动',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.immediate.transfer',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(self.env.ref('amazon_api.b2b_stock_immediate_transfer_form').id, 'form')],
            'target': 'new',
        }

    # @api.multi
    # def do_new_transfer(self):
    #     self.ensure_one()
    #     # print self.b2b_type
    #     # if self.b2b_type == 'internal':
    #     #     return {
    #     #         'name': u'调拨',
    #     #         'type': 'ir.actions.act_window',
    #     #         'res_model': 'stock.immediate.transfer',
    #     #         'view_mode': 'form',
    #     #         'view_type': 'form',
    #     #         'views': [(self.env.ref('amazon_api.b2b_stock_immediate_transfer_form').id, 'form')],
    #     #         'target': 'new',
    #     #     }
    #     result = super(StockPicking, self).do_new_transfer()
    #     return result
    #     self.create_delivery_info()
    #     self.write({
    #         'b2b_state': 'done',
    #         'delivery_date': datetime.datetime.now(),
    #     })
    #     self.purchase_order_id.platform_purchase_state = 'done'
    #     self.sale_order_id.sudo().b2b_invoice_ids.invoice_confirm()
    #     self.purchase_order_id.sudo().b2b_invoice_ids.invoice_confirm()
    #     done = True
    #     for purchase in self.sale_order_id.purchase_orders:
    #         if purchase.platform_purchase_state != 'done':
    #             done = False
    #     if done:
    #         self.sale_order_id.b2b_state = 'delivered'
    #     return result

    @api.multi
    def unlink(self):
        for record in self:
            if record.pack_operation_product_ids:
                record.pack_operation_product_ids.unlink()
        result = super(StockPicking, self).unlink()
        return result

    @api.multi
    def upload_delivery_info(self):
        '''上传发货信息至亚马逊'''
        self.ensure_one()
        if not self.logistics_company_id:
            raise UserError(u'请填写物流公司！')
        if not self.shippment_number:
            raise UserError(u'请填写物流单号！')
        purchase = self.sudo().purchase_order_id
        if not purchase:
            raise UserError(u'Not found purchase order!')
        sale_order = purchase.sale_order_id
        if not sale_order:
            raise UserError(u'Not found sale order!')
        shop = sale_order.sudo().shop_id
        seller = shop.seller_id
        marketplaceids = [shop.marketplace_id.marketplace_id]
        AmazonOrderID = sale_order.e_order
        FulfillmentDate = (datetime.datetime.now() - datetime.timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%S') + \
                          '-00:00'
        message_id = 0
        message_info = ''
        for picking_line in self.pack_operation_product_ids:
            sale_line = picking_line.b2b_sale_line_id
            message_id += 1
            message_info += """<Message>
                    <MessageID>%d</MessageID>
                    <OperationType>Update</OperationType>
                    <OrderFulfillment>
                        <AmazonOrderID>%s</AmazonOrderID>
                        <FulfillmentDate>%s</FulfillmentDate>
                        <FulfillmentData>
                            <CarrierName>%s</CarrierName>
                            <ShippingMethod>%s</ShippingMethod>
                            <ShipperTrackingNumber>%s</ShipperTrackingNumber>
                        </FulfillmentData>
                        <Item>
                            <AmazonOrderItemCode>%s</AmazonOrderItemCode>
                            <Quantity>%s</Quantity>
                        </Item>
                    </OrderFulfillment>
                </Message>""" % (message_id, AmazonOrderID, FulfillmentDate,
                                 self.logistics_company_id.name, sale_order.shipment_service_level_category,
                                 self.shippment_number, sale_line.order_item_id, int(picking_line.qty_done))
        head = """<?xml version="1.0" encoding="utf-8"?>
                <AmazonEnvelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="amzn-envelope.xsd">
                    <Header>
                        <DocumentVersion>1.01</DocumentVersion>
                            <MerchantIdentifier>%s</MerchantIdentifier>
                    </Header>
                    <MessageType>OrderFulfillment</MessageType>
                    %s
                </AmazonEnvelope>""" % (seller.merchant_id_num, message_info)
        print sale_order,shop,shop.country_id,shop.country_id.code
        mws_obj = Feeds(access_key=str(seller.access_key), secret_key=str(seller.secret_key),
                        account_id=str(seller.merchant_id_num), region=shop.country_id.code, proxies={})
        try:
            result = mws_obj.submit_feed(head, '_POST_ORDER_FULFILLMENT_DATA_', marketplaceids=marketplaceids)
        except Exception, e:
            raise UserError(str(e))
        FeedSubmissionId = result.parsed.get('FeedSubmissionInfo', {}).get('FeedSubmissionId', {}).get('value', '')
        if FeedSubmissionId:
            self.env['submission.history'].create({
                'model': 'stock.picking',
                'record_id': self.id,
                'feed_id': FeedSubmissionId,
                'feed_time': datetime.datetime.now(),
                'feed_xml': head,
                'shop_id': shop.id,
                'type': 'delivery_info_upload_state'
            })
        self.delivery_info_upload_state = 'uploading'

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
    #     context = self.env.context or {}
    #     if context.get('view_own_picking'):
    #         merchant_id = self.env.user.merchant_id or self.env.user
    #         if self.user_has_groups('b2b_platform.b2b_shop_operator'):
    #             args += [('partner_id', '=', merchant_id.partner_id.id)]
    #         elif self.user_has_groups('b2b_platform.b2b_seller'):
    #             args += [('partner_id', '=', merchant_id.partner_id.id)]
    #         elif self.user_has_groups('b2b_platform.b2b_manager'):
    #             pass
    #         else:
    #             pass
    #     return super(StockPicking, self).search(args, offset, limit, order, count=count)

    @api.multi
    def _own_record(self):
        merchant = self.env.user.merchant_id or self.env.user
        for record in self:
            if record.partner_id == merchant.partner_id:
                record.own_record = True
            else:
                record.own_record = False