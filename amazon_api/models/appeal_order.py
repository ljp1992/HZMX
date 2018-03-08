# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime

class AppealOrder(models.Model):
    _name = 'appeal.order'
    _order = 'id desc'

    name = fields.Char(string=u'单号')

    appeal_text = fields.Text(string=u'申诉内容')
    answer_text = fields.Text(string=u'答复')
    platform_note = fields.Text(string=u'平台备注')

    submitted_appeal = fields.Boolean(search='_search_submitted_appeal', store=False)
    received_appeal = fields.Boolean(search='_search_received_appeal', store=False)

    appeal_time = fields.Datetime(default=lambda self: datetime.datetime.now(),string=u'申诉日期')

    appeal_amount = fields.Float(required=True, string=u'申诉退款金额')
    agree_amount = fields.Float(string=u'同意退款金额')

    sale_order_id = fields.Many2one('sale.order', domain=lambda self: self._get_sale_order_domain(), string=u'销售订单')
    purchase_id = fields.Many2one('purchase.order', string=u'采购单')
    picking_id = fields.Many2one('stock.picking', string=u'发货单')
    supplier_id = fields.Many2one('res.partner', related='purchase_id.partner_id', store=True,
                                  readonly=True, string=u'供应商')
    distributor_id = fields.Many2one('res.partner', related='sale_order_id.merchant_id.partner_id', store=True,
                                     readonly=True, string=u'经销商')

    transaction_details = fields.One2many('transaction.detail', 'appeal_id')

    state = fields.Selection([
        ('draft', u'草稿'),
        ('wait_supplier_confirm', u'待供应商审核'),
        ('wait_platform_confirm', u'待平台审核'),
        ('done', u'完成'),
        ('fail', u'申诉失败'),
    ], default='draft', required=True, string=u'状态')
    identity = fields.Selection([
        ('distributor', u'经销商'),
        ('supplier', u'供应商'),
        ('manager', u'管理员'),
    ], compute='_compute_identity', sotre=False, string=u'身份')

    @api.model
    def _get_sale_order_domain(self):
        user = self.env.user
        if self.user_has_groups('b2b_platform.b2b_shop_operator'):
            return [('shop_id', 'in', user.shop_ids.ids)]
        elif self.user_has_groups('b2b_platform.b2b_seller'):
            return [('merchant_id', '=', self.env.user.id)]
        else:
            return [('id', '=', 0)]

    @api.model
    def _search_submitted_appeal(self, operation, value):
        merchant = self.env.user.merchant_id or self.env.user
        return [('distributor_id', '=', merchant.partner_id.id)]

    @api.model
    def _search_received_appeal(self, operation, value):
        merchant = self.env.user.merchant_id or self.env.user
        return [('supplier_id', '=', merchant.partner_id.id)]

    @api.multi
    def submit_appeal_order(self):
        self.ensure_one()
        self.state = 'wait_supplier_confirm'

    @api.multi
    def supplier_confirm(self):
        '''供应商确认申诉单'''
        self.ensure_one()
        if self.agree_amount == self.appeal_amount:
            self.state = 'done'
            self.create_transcation_detail()
        else:
            self.state = 'wait_platform_confirm'

    @api.multi
    def supplier_refuse(self):
        '''供应商拒绝'''
        self.ensure_one()
        self.state = 'wait_platform_confirm'

    @api.multi
    def platform_confirm(self):
        '''平台协调确认'''
        self.ensure_one()
        self.state = 'done'
        self.create_transcation_detail()

    @api.multi
    def platform_refuse(self):
        '''平台驳回申诉单'''
        self.ensure_one()
        self.state = 'fail'

    @api.multi
    def create_transcation_detail(self):
        '''创建交易记录'''
        for record in self:
            distributor = self.env['res.users'].search([('partner_id', '=', record.distributor_id.id)], limit=1)
            if distributor:
                self.env['transaction.detail'].create({
                    'origin': record.name,
                    'paid_time': datetime.datetime.now(),
                    'amount': record.agree_amount,
                    'merchant_id': distributor.id,
                    'appeal_id': record.id,
                    'type': 'submitted_appeal',
                    'state': 'done',
                })
            supplier = self.env['res.users'].search([('partner_id', '=', record.supplier_id.id)], limit=1)
            if supplier:
                self.env['transaction.detail'].create({
                    'origin': record.name,
                    'paid_time': datetime.datetime.now(),
                    'amount': record.agree_amount,
                    'merchant_id': supplier.id,
                    'appeal_id': record.id,
                    'type': 'received_appeal',
                    'state': 'done',
                })

    @api.multi
    def _compute_identity(self):
        for record in self:
            if self.user_has_groups('b2b_platform.b2b_shop_operator') or \
                    self.user_has_groups('b2b_platform.b2b_seller'):
                merchant = self.env.user.merchant_id or self.env.user
                if record.distributor_id == merchant.partner_id:
                    record.identity = 'distributor'
                elif record.supplier_id == merchant.partner_id:
                    record.identity = 'supplier'
            elif self.user_has_groups('b2b_platform.b2b_manager'):
                record.identity = 'manager'

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        sale_order = self.sale_order_id
        if len(sale_order.purchase_orders) == 1:
            purchase_id = sale_order.purchase_orders.id
        else:
            purchase_id = False
        if len(sale_order.agent_deliverys) == 1:
            picking_id = sale_order.agent_deliverys.id
        else:
            picking_id = False
        if sale_order:
            return {
                'value': {
                    'purchase_id': purchase_id,
                    'picking_id': picking_id,
                    'distributor_id': sale_order.merchant_id.partner_id.id,
                },
                'domain': {
                    'purchase_id': [('id', 'in', sale_order.purchase_orders.ids or [])],
                    'picking_id': [('id', 'in', sale_order.agent_deliverys.ids or [])],
                }
            }
        else:
            return {
                'value': {

                }
            }

    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        return {
            'value': {
                'supplier_id': self.picking_id and self.picking_id.partner_id.id or False,
            }
        }

    @api.onchange('purchase_id')
    def _onchange_purchase_id(self):
        self.supplier_id = self.purchase_id and self.purchase_id.partner_id.id or False

    @api.model
    def create(self, val):
        if not val.has_key('name'):
            val['name'] = self.env['ir.sequence'].next_by_code('appeal.order.number') or '/'
        result = super(AppealOrder, self).create(val)
        result.check_appeal_order()
        return result

    @api.multi
    def write(self, val):
        result = super(AppealOrder, self).write(val)
        self.check_appeal_order()
        return result

    @api.multi
    def unlink(self):
        merchant = self.env.user.merchant_id or self.env.user
        for record in self:
            if merchant.partner_id != record.distributor_id:
                raise UserError(u'该用户没有删除该单据的权限!')
            record.transaction_details.unlink()
        return super(AppealOrder, self).unlink()

    @api.multi
    def check_appeal_order(self):
        '''检查申诉单是否合法'''
        for record in self:
            if self.purchase_id not in self.sale_order_id.purchase_orders:
                raise UserError(u'该采购单不属于该销售订单！')
            if self.picking_id not in self.purchase_id.deliverys:
                raise UserError(u'该发货单不属于该采购单！')
            if record.agree_amount > record.appeal_amount:
                raise UserError(u'同意退款金额不能大于申诉退款金额！')
