# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ResUsers(models.Model):
    _inherit = 'res.users'

    audit_state = fields.Selection([
        ('waiting', u'待审核'),
        ('pass', u'审核通过'),
        ('failed', u'未审核通过')
    ], string=u'审核状态')

    @api.multi
    def pass_audit(self):
        self.ensure_one()
        self.groups_id = [(4, self.env.ref('b2b_platform.b2b_seller').id)]

    # def unlink(self):
    #     '''删除user，同时也删除partner'''
    #     partner_ids = []
    #     for user in self:
    #         partner_ids.append(user.partner_id.id)
    #     partners = self.env['res.partner'].browse(partner_ids)
    #     print partners
    #     result = super(ResUsers, self).unlink()
    #     print partners
    #     partners.unlink()
    #     print partners
    #     raise UserError('11')
    #     return result