from marshmallow import Schema, fields, post_load, EXCLUDE
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Date, Float, Numeric, text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Stock(Base):
    __tablename__ = 'stock'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(8))
    name = Column(String(50))
    industry = Column(String(30))  # TODO
    price = Column(Numeric(10, 2))
    altUrl = Column(String(100))
    updatedAt = Column(DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    currencyId = Column(Integer, ForeignKey("currency.id"), nullable=False)
    currency = relationship('Currency', back_populates="stocks")
    marketOrders = relationship('MarketOrder', back_populates="stock")

    def __repr__(self):
        return f'Stock(id={self.id!r}, ticker={self.ticker!r}, name={self.name!r}, currency={self.currency!r})'

class Region(Base):
    __tablename__ = 'region'
    # __table_args__ = {'comment': 'List of stock exchanges'}
    id = Column(Integer, primary_key=True)
    name = Column(String(30))  # comment='Name of stock exchange'
    currencyId = Column(Integer, ForeignKey("currency.id"), nullable=False)
    currency = relationship('Currency', uselist=False, back_populates="region")
    portfolio = relationship('Portfolio', back_populates="region")
    marketOrders = relationship('MarketOrder', back_populates="region")  # cascade="all, delete-orphan"

    def __repr__(self):
        return f'Region(id={self.id!r}, name={self.name!r})'

class Currency(Base):
    __tablename__ = 'currency'
    id = Column(Integer, primary_key=True)
    shortName = Column(String(8))
    fullName = Column(String(30))
    sgdConversion = Column(Numeric(10, 5))
    updatedAt = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    region = relationship('Region', uselist=False, back_populates="currency")
    stocks = relationship('Stock', back_populates="currency")

    def __repr__(self):
        return f'Currency(id={self.id!r}, shortName={self.shortName!r}, fullName={self.fullName!r})'

class MarketOrder(Base):
    __tablename__ = 'marketOrder'
    id = Column(Integer, primary_key=True)
    buyDate = Column(Date)
    cumulativeUnits = Column(Numeric(10, 2))
    units = Column(Numeric(10, 4))
    price = Column(Numeric(10, 2))
    fees = Column(Numeric(10, 2), server_default=text("0"))
    # sgdConversion = Column(Numeric(10, 2))
    regionId = Column(Integer, ForeignKey("region.id"), nullable=False)
    stockId = Column(Integer, ForeignKey("stock.id"), nullable=False)
    region = relationship('Region', back_populates="marketOrders")
    stock = relationship('Stock', back_populates="marketOrders")

    def __repr__(self):
        return f'Order(id={self.id!r}, stock={self.stock!r}, price={self.price!r}, stock={self.stock!r}, region={self.region!r})'

class Portfolio(Base):
    __tablename__ = 'portfolio'
    id = Column(Integer, primary_key=True)
    costValue = Column(Numeric(10, 2))
    marketValue = Column(Numeric(10, 2))
    marketDiff = Column(Numeric(10, 2))
    sgdConversion = Column(Numeric(10, 5))
    costValueSGD = Column(Numeric(10, 2))
    marketValueSGD = Column(Numeric(10, 2))
    marketDiffSGD = Column(Numeric(10, 2))
    updatedAt = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    regionId = Column(Integer, ForeignKey("region.id"), nullable=False)
    region = relationship('Region', back_populates="portfolio")

    def __repr__(self):
        return f'Portfolio(id={self.id!r})'

# class StockSchema(Schema):
#     # id = fields.Integer(required=True)
#     ticker = fields.String(required=True)
#     name = fields.String(required=True)
#     industry = fields.String(required=True)  #
#     price = fields.Float(places=2)
#     altUrl = fields.String(required=True)
#     currency = fields.Field()

#     @post_load
#     def return_object(self, data, **kwargs):
#         currency = data.pop('currency')
#         return Stock(**data, currency=currency)
