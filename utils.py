from timeit import default_timer   # from time import time
from functools import wraps
import pendulum

def timeTaken(f):
    @wraps(f)
    def wrap(*args, **kw):
        t1 = default_timer()
        result = f(*args, **kw)
        timeTaken = default_timer()-t1
        # print('func:%r args:[%r, %r] took: %2.4f sec' % (f.__name__, args, kw, timeTaken))
        args = "','".join(map(str, args))
        print(f'[{pendulum.now()}] Time taken for {f.__name__}({repr(args)}): {timeTaken:2.4f} s')
        return result
    return wrap

from marshmallow import Schema, fields, post_load, EXCLUDE
from sqlalchemy import create_engine, MetaData, Column, ForeignKey, Integer, String, DateTime, Date, text
from sqlalchemy.orm import declarative_base, relationship, Session
from sqlalchemy.schema import FetchedValue
from urllib.parse import quote
import logging
import json

from cryptography.fernet import Fernet
import yaml
import json
import os

import requests
import re

def getCredentials(name):
    if not os.getenv('KEY'):
        raise Exception('no KEY in env')
    if not os.getenv(f'SECRET_{name}'):
        raise Exception(f'no SECRET_{name} in env')
    key = bytes(os.getenv('KEY'), 'utf-8')
    encrypted = bytes(os.getenv(f'SECRET_{name}'), 'utf-8')
    # return json.loads(Fernet(key).decrypt(encrypted))
    return yaml.safe_load(Fernet(key).decrypt(encrypted))

def customLogger(app):
    # print(__name__, __file__)
    logger = logging.getLogger(app)
    logger.setLevel(level=logging.INFO)
    handler = logging.FileHandler(filename=app.replace('.py', '.log'), mode='a', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

class YahooFinance():
    headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Mobile Safari/537.36',
    }

    @staticmethod
    def getCurrencyConversion(target, base='SGD'):
        if target == base: return 1.0
        url = 'https://api.rates-history-service.prd.aws.ofx.com/rate-history/api/1'
        payload = {"method":"spotRateHistory","data":{"base":base,"term":target,"period":"day"}}
        response = requests.post(url, headers=YahooFinance.headers, json=payload)
        if response.ok:
            return response.json()['data']['CurrentInterbankRate']
        else:
            logging.info(f'Conversion not found: {base} -> {target}')
            return None

    @staticmethod
    def getPriceTEST(ticker):
        headers = {
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Mobile Safari/537.36',
            'cookie': 'A1=d=AQABBO2rGmYCEL2Okw0AUuK9J9t01GbXxjcFEgEBCAEFa2aVZq-0b2UB_eMBAAcI7asaZmbXxjc&S=AQAAAnjV1lgzk6KDt_fnUv-_LlI',
        }
        url = f'https://query1.finance.yahoo.com/v7/finance/quote?fields=longName%2CregularMarketPrice%2CregularMarketChange%2CregularMarketChangePercent%2CshortName%2CpriceHint&formatted=true&imgHeights=50&imgLabels=logoUrl&imgWidths=50&symbols={ticker}&lang=en-US&region=US&crumb=%2FrR.u0fZrvx'
        response = requests.get(url, headers=headers)
        print(response.text)

    @staticmethod
    def getPriceHTML(ticker):
        # has tickerName
        url = f'https://finance.yahoo.com/quote/{ticker}'
			# <script type="application/json" data-sveltekit-fetched data-url="https://query1.finance.yahoo.com/v7/finance/quote?fields=fiftyTwoWeekHigh%2CfiftyTwoWeekLow%2CfromCurrency%2CfromExchange%2CheadSymbolAsString%2ClogoUrl%2ClongName%2CmarketCap%2CmessageBoardId%2CoptionsType%2CregularMarketTime%2CregularMarketChange%2CregularMarketChangePercent%2CregularMarketOpen%2CregularMarketPrice%2CregularMarketSource%2CregularMarketVolume%2CpostMarketTime%2CpostMarketPrice%2CpostMarketChange%2CpostMarketChangePercent%2CpreMarketTime%2CpreMarketPrice%2CpreMarketChange%2CpreMarketChangePercent%2CshortName%2CtoCurrency%2CtoExchange%2CunderlyingExchangeSymbol%2CunderlyingSymbol&amp;formatted=true&amp;imgHeights=50&amp;imgLabels=logoUrl&amp;imgWidths=50&amp;symbols=RPI.L&amp;lang=en-US&amp;region=US&amp;crumb=qBCyczpZL31" data-ttl="1">
        response = requests.get(url, headers=YahooFinance.headers)
        if response.ok:
            res = re.search(f'<script[^>]*v7/finance/quote.*symbols={ticker}&[^>]*>([^<]*)', response.text)
            if res:
                response = json.loads(res.group(1))
                metadata = json.loads(response['body'])['quoteResponse']['result'][0]
                price = metadata['regularMarketPrice']['raw']
                currency = metadata['currency']
                symbol = metadata['symbol']
                return symbol, price, currency
        else:
            if ticker == 'VMW':
                return ticker, 0, 'USD'
            raise Exception(f'{ticker} - {response.text}')

    @staticmethod
    def getPriceAPI(ticker):
        timestamp = int(pendulum.now(tz='Asia/Singapore').timestamp())
        url = f'https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?period1={timestamp-200}&period2={timestamp}&\
            interval=1m&includePrePost=true&events=div%7Csplit%7Cearn&&lang=en-US&region=US'
        response = requests.get(url, headers=YahooFinance.headers)
        if response.ok:
            data = response.json()
            metadata = data['chart']['result'][0]['meta']
            price = metadata['regularMarketPrice']
            currency = metadata['currency']
            symbol = metadata['symbol']
            return symbol, price, currency
        else:
            if ticker == 'VMW':
                return ticker, 0, 'USD'
            raise Exception(f'{ticker} - {response.text}')

    @staticmethod
    def getStockAPI(ticker):
        # TODO : handle market=None
        url = f'https://query2.finance.yahoo.com/v1/finance/quoteType/?symbol={ticker}'
        response = requests.get(url, headers=YahooFinance.headers)
        if response.ok:
            try:
                data = response.json()
                if data['quoteType']['result']:
                    return data['quoteType']['result'][0]['longName'], data['quoteType']['result'][0]['market'].split('_')[0].upper()
                else:
                    if ticker == 'VMW':
                        return ticker, 'US'
                    else:
                        raise Exception(f'no market for {ticker}')
            except Exception as e:
                # logging.info(f'{ticker} - {e}')
                raise Exception(f'{ticker} - {e}')
        else:
            logging.info(f'{ticker} - {response.text}')
            return ticker, None

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--ticker', type=str, default='RPI.L')
    parser.add_argument('--currency', type=str, default='GBP')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    if 0:
        if 1:
            YahooFinance.getPriceTEST(args.ticker)
        else:
            YahooFinance.getPriceAPI(args.ticker)
            YahooFinance.getPriceHTML(args.ticker)
    else:
        # add stock
        from sql import getEngine
        if args.debug:
            engine = getEngine('test')
        else:
            engine = getEngine('prod')

        with Session(engine) as session:
            from models import Currency, Stock
            currency = session.query(Currency).filter_by(shortName=args.currency).one()
            name, region = YahooFinance.getStockAPI(args.ticker)
            symbol, price, currency = YahooFinance.getPriceAPI(args.ticker)
            try:
                currency = session.query(Currency).filter_by(shortName=currency).one()
            except Exception as e:
                raise Exception(f'{args.ticker}, {symbol}, {price}, {currency} - {e}')
            session.add(Stock(ticker=symbol, name=name,price=price,currency=currency))
            session.commit()