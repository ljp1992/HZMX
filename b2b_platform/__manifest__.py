# -*- coding: utf-8 -*-
{
    'name': "b2b_platform",

    'summary': """
        """,

    'description': """
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'sale', 'purchase', 'account', 'website', 'website_sale', 'web_tree_image',
                'web_form_image', 'document_multi_upload', 'web_export_view', 'l10n_cn_standard',
                'currency_rate_update', 'vieterp_mailbox'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'data/stock_location.xml',
        'data/ir_sequence.xml',
        'views/menu.xml',
        'views/res_users.xml',
        'views/auth_signup.xml',
        'views/res_bank.xml',
        'views/bank_account.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'application': True,
}