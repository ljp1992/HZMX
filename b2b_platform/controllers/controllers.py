# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute
from odoo.addons.website.models.website import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.website_portal.controllers.main import website_account
import base64
from odoo.exceptions import UserError

import logging
import werkzeug

_logger = logging.getLogger(__name__)

PPG = 20  # Products Per Page
PPR = 4   # Products Per Row


class AuthSignupHomeNew(AuthSignupHome):

    def do_signup(self, qcontext):
        '''写入res_partner category_id值  Modefied by 刘吉平 on 2018-01-03'''
        # assert qcontext.get('password'), u"请输入密码！"
        super(AuthSignupHomeNew, self).do_signup(qcontext)
        user = request.env['res.users'].sudo().search([('login', '=', qcontext.get('login'))])
        if user:
            user.write({
                'user_type': 'merchant',
                'audit_state': 'waiting',
                'phone': qcontext.get('mobile'),
                'introduction': qcontext.get('introduction'),
            })

