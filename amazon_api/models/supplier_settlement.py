# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime

class SupplierSettlement(models.Model):
    _name = 'supplier.settlement'
    _order = 'id desc'

    name = fields.Char(string=u'单号')

    note = fields.Text(string=u'备注')

    own_data = fields.Boolean(search='_own_data', store=False)

    from_date = fields.Datetime(default=lambda self: datetime.datetime.now() - datetime.timedelta(days=30),
                                string=u'起始时间')
    to_date = fields.Datetime(default=lambda self: datetime.datetime.now(), string=u'终止时间')

    merchant_id = fields.Many2one('res.users', string=u'供应商', required=True, domain=[('user_type', '=', 'merchant')])

    order_line = fields.One2many('invoice', 'supplier_settlement_id')

    state = fields.Selection([
        ('draft', u'草稿'),
        ('wait_supplier_confirm', u'待供应商确认'),
        ('done', u'完成'),
    ], default='draft', string=u'状态')

    @api.model
    def _own_data(self, operation, value):
        merchant = self.env.user.merchant_id or self.env.user
        if self.user_has_groups('b2b_platform.b2b_shop_operator'):
            return [('merchant_id', '=', merchant.id)]
        elif self.user_has_groups('b2b_platform.b2b_seller'):
            return [('merchant_id', '=', merchant.id)]

    @api.model
    def create(self, val):
        if not val.has_key('name'):
            val['name'] = self.env['ir.sequence'].next_by_code('supplier.settlement.number') or '/'
        return super(SupplierSettlement, self).create(val)

    def action_confirm(self):
        self.ensure_one()
        self.state = 'done'
        self.order_line.invoice_confirm()

    def action_send(self):
        self.ensure_one()
        self.state = 'wait_supplier_confirm'

    @api.multi
    def search_supplier_invoice(self):
        self.ensure_one()
        self.order_line = False
        invoices = self.env['invoice'].sudo().search([
            ('state', '=', 'draft'),
            ('type', '=', 'supplier'),
            ('create_date', '>=', self.from_date),
            ('create_date', '<=', self.to_date),
        ])
        invoices.write({
            'supplier_settlement_id': self.id,
        })


