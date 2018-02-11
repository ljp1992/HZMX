# -*- coding: utf-8 -*-


seller_marketplace = {'ListParticipations':
     {'Participation': [
         {
             'HasSellerSuspendedListings': {'value': 'No'},
             'SellerId': {'value': 'A2YUAAEMOGAIQV'}, 'value': '\n        ',
             'MarketplaceId': {'value': 'A1AM78C64UM0Y8'}
         },
         {
             'HasSellerSuspendedListings': {'value': 'No'},
             'SellerId': {'value': 'A2YUAAEMOGAIQV'}, 'value': '\n        ',
             'MarketplaceId': {'value': 'A2EUQ1WTGCTBG2'}},
         {
             'HasSellerSuspendedListings': {'value': 'No'},
             'SellerId': {'value': 'A2YUAAEMOGAIQV'}, 'value': '\n        ',
             'MarketplaceId': {'value': 'ATVPDKIKX0DER'}}], 'value': '\n      '},
    'ListMarketplaces': {
        'Marketplace': [
            {
                'DefaultCountryCode': {'value': 'MX'},
                'Name': {'value': 'Amazon.com.mx'},
                'DomainName': {'value': 'www.amazon.com.mx'},
                'DefaultLanguageCode': {'value': 'es_MX'}, 'value': '\n        ',
                'DefaultCurrencyCode': {'value': 'MXN'},
                'MarketplaceId': {'value': 'A1AM78C64UM0Y8'}},
            {
                'DefaultCountryCode': {'value': 'CA'},
                'Name': {'value': 'Amazon.ca'},
                'DomainName': {'value': 'www.amazon.ca'},
                'DefaultLanguageCode': {'value': 'en_CA'}, 'value': '\n        ',
                'DefaultCurrencyCode': {'value': 'CAD'}, 'MarketplaceId': {'value': 'A2EUQ1WTGCTBG2'}}, {'DefaultCountryCode': {'value': 'US'}, 'Name': {'value': 'Amazon.com'}, 'DomainName': {'value': 'www.amazon.com'}, 'DefaultLanguageCode': {'value': 'en_US'}, 'value': '\n        ', 'DefaultCurrencyCode': {'value': 'USD'}, 'MarketplaceId': {'value': 'ATVPDKIKX0DER'}}], 'value': '\n      '}, 'value': '\n    '}

print seller_marketplace.keys()
print seller_marketplace.get('ListMarketplaces', {}).keys()
for item in seller_marketplace.get('ListMarketplaces', {}).get('Marketplace', []):
    country_code = item.get('DefaultCountryCode', {}).get('value', '')
    currency_code = item.get('DefaultCurrencyCode', {}).get('value', '')
    language_code = item.get('DefaultLanguageCode', {}).get('value', '')
    name = item.get('Name', {}).get('value', '')
    domain_name = item.get('DomainName', {}).get('value', '')
    marketplace_id = item.get('MarketplaceId', {}).get('value', '')
    print country_code,currency_code,language_code,marketplace_id