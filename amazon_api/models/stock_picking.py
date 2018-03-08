# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime
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

    delivery_date = fields.Datetime(string=u'发货时间')

    # own_data = fields.Boolean(search='_own_data_search', store=False)
    b2b_log_count = fields.Integer(compute='_b2b_log_count')

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
    # distributor_invoice_ids = fields.Many2one('invoice', related='sale_order_id.invoice_ids', string=u'经销商发票')

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
    ], string=u'类型')

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
        sale_order = self.sudo().sale_order_id
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