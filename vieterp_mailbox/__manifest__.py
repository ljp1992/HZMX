# -*- coding: utf-8 -*-
{
    'name': "VietERP Mailbox",

    'summary': """
        Simple Odoo mailbox""",

    'description': """
1. Main features:
    - Sending email from odoo
    - Receiving email from odoo
    - Composing email from odoo
    - Choosing template when composing email

2. Why choose this?
    - Quickly compose email by using template
    - Don't need to setup any email client on computer
    - Can access it from any where

3. Settings:
    - To receiving email, you should follow below:
    Step1:
    <img src="/vieterp_mailbox/static/description/step1.png"/>
    Step2:
    <img src="/vieterp_mailbox/static/description/step2.png"/>
    Step3:
    <img src="/vieterp_mailbox/static/description/step3.png"/>

4. Support:
    For any feedback, please send email to info@vieterp.net

    """,

    'author': "VietERP / Sang",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Discuss',
    'version': '1.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'mail',
    ],

    # always loaded
    'data': [
        'data/cron.xml',
        'data/data.xml',
        'security/record_rules.xml',
        'security/ir.model.access.csv',
        'views/mail_mail_views.xml',
        'views/fetchmail_server_views.xml',
        'views/mail_server_source_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
}
