# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.osv import osv
from datetime import datetime
from odoo.exceptions import ValidationError, UserError

class AccountCharge(models.Model):
    _inherit = 'account.charge'


    transcation_detail_ids = fields.One2many('transcation.detail', 'charge_id')

    @api.model
    def create(self, val):
        if not val.has_key('name'):
            val['name'] = self.env['ir.sequence'].next_by_code('account.charge.number') or '/'
        result = super(AccountCharge, self).create(val)
        result.create_transcation_detail()
        return result

    @api.multi
    def create_transcation_detail(self):
        for record in self:
            val = {
                'origin': record.name,
                'charge_id': record.id,
                'type': 'charge',
                'state': 'draft',
                'amount': record.amount,
            }
            print record.amount
            self.env['transcation.detail'].create(val)



