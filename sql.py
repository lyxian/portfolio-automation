from sqlalchemy import create_engine, MetaData, func
from sqlalchemy.orm import Session, sessionmaker
from urllib.parse import quote
import pendulum
import argparse
import logging

from utils import getCredentials, YahooFinance, timeTaken

def getEngine(env='test'):
    handler = logging.FileHandler('sqlalchemy.log', mode='a')
    # handler = logging.FileHandler('sqlalchemy.log', mode='w')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    logging.getLogger('sqlalchemy').addHandler(handler)

    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(level=logging.INFO)
    logging.getLogger().info('\n\n--- START ---')
    logging.getLogger().handlers = []

    dbInfo = getCredentials('MARIADB')
    if not env in dbInfo['dbName']:
        raise Exception(f'invalid env-{env}')
    dbName = dbInfo['dbName'][env]
    host, port, user, _pass = [v for k,v in dbInfo['mariadb'].items()]
    engine = create_engine(
        f'mariadb+mariadbconnector://{user}:{quote(_pass)}@{host}:{port}/{dbName}', 
        echo=True, pool_pre_ping=True)

    # engineHandler = engine.logger.logger.handlers[0]
    engine.logger.logger.handlers = []

    return engine

@timeTaken
def initDB(env):
    engine = getEngine(env)
    from models import Base
    Base.metadata.drop_all(engine) 
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        from init.sql import data
        from models import Currency, Stock, Region, MarketOrder
        
        
        session.add_all([Currency(**currency, sgdConversion=YahooFinance.getCurrencyConversion(currency['shortName'])) 
            for currency in data[env]['currency']])

        regions = []
        for stock in data[env]['stock']:
            name, region = YahooFinance.getStockAPI(stock)
            symbol, price, currency = YahooFinance.getPriceAPI(stock)
            try:
                currency = session.query(Currency).filter_by(shortName=currency).one()
            except Exception as e:
                raise Exception(f'{stock}, {symbol}, {price}, {currency} - {e}')
            
            if region not in regions:   # region = Session.query(Region).filter_by(name=name).all()
                session.add(Region(name=region, currency=currency))
                regions += [region]
            session.add(Stock(ticker=symbol, name=name,price=price,currency=currency))

        for order in data[env]['order']:
            # TODO : handle error for .one()
            region = session.query(Region).filter_by(name=order['region']).one()
            stock = session.query(Stock).filter_by(ticker=order['stock']).one()
            cumulativeUnits = order['units'] + float(sum([i.units for i in session.query(MarketOrder).filter_by(stock=stock).all()]))
            payload = {
                **order,
                'buyDate': pendulum.from_format(order['buyDate'], 'M/DD/YYYY').format('YYYY-MM-DD'),
                'cumulativeUnits': cumulativeUnits,
                'region': region,
                'stock': stock,
            }
            order = MarketOrder(**payload)
            session.add(order)
        
        session.commit()

        portfolioSnapshot(session, checkPrice=False)

# ---
@timeTaken
def portfolioSnapshot(session, checkPrice=True):
    # Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    from models import Stock, Currency, MarketOrder, Portfolio
    if checkPrice:
        for currency in session.query(Currency).all():
            currency.sgdConversion = YahooFinance.getCurrencyConversion(currency.shortName)
            session.add(currency)
        session.commit()
        for stock in session.query(Stock).all():
            _, stock.price, _ = YahooFinance.getPriceAPI(stock.ticker)
            session.add(stock)
        session.commit()
    portfolio = {}
    for order in session.query(MarketOrder).all():
        if order.region.id in portfolio:
            portfolio[order.region.id]['costValue'] += order.price * order.units
            portfolio[order.region.id]['marketValue'] += order.stock.price * order.units
        else:
            portfolio[order.region.id] = {
                'sgdConversion': order.stock.currency.sgdConversion,
                'costValue': order.price * order.units,
                'marketValue': order.stock.price * order.units
            }
    
    for regionId in portfolio:
        sgdConversion = portfolio[regionId]['sgdConversion']
        costValue = portfolio[regionId]['costValue']
        marketValue = portfolio[regionId]['marketValue']
        marketDiff = marketValue - costValue
        costValueSGD = costValue / sgdConversion
        marketValueSGD = marketValue / sgdConversion
        marketDiffSGD = marketValueSGD - costValueSGD
        session.add(Portfolio(costValue=costValue, marketValue=marketValue, marketDiff=marketDiff, sgdConversion=sgdConversion,
            costValueSGD=costValueSGD,marketValueSGD=marketValueSGD,marketDiffSGD=marketDiffSGD, regionId=regionId))
    session.commit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--init', action='store_true')
    parser.add_argument('--prod', action='store_true')
    args = parser.parse_args()
    if args.init:
        if args.prod:
            initDB('prod')
        else:
            initDB('test')
        print('init ok')
    else:
        # test update
        # - get all stocks >> get current price >> snapshot portfolio
        engine = getEngine('prod')
        
        with Session(engine) as session:
            if args.prod:
                portfolioSnapshot(session)
            else:
                from models import Stock, Currency, Region, MarketOrder, Portfolio
                y = MarketOrder ; print()
                for item in session.query(y).all():
                    print(item)
                    print(item.region)
                    print(item.stock)
                y = Stock ; print()
                for item in session.query(y).all():
                    print(item)
                    print(item.currency)
                    print(item.marketOrders)
                y = Region ; print()
                for item in session.query(y).all():
                    print(item)
                    print(item.currency)
                    print(item.portfolio)
                    print(item.marketOrders)
                y = Currency ; print()
                for item in session.query(y).all():
                    print(item)
                    print(item.region)
                    print(item.stocks)
                    print(item.marketOrders)
                y = Portfolio ; print()
                for item in session.query(y).all():
                    print(item)
                    print(item.region)
