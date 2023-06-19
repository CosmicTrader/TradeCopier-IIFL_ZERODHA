#import all necessary libraries
from sqlalchemy import Column, String, Integer, Float, TIMESTAMP, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Parent_Order(Base):
    __tablename__ = 'parent_order'
    id = Column(Integer, primary_key= True)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    ClientID = Column(String(20))
    AppOrderID = Column(String(30))
    TradingSymbol = Column(String(30))
    OrderCategoryType = Column(String(20))
    ExchangeSegment = Column(String(10))
    ExchangeInstrumentID = Column(String(10))
    OrderSide = Column(String(10))
    OrderType = Column(String(15))
    ProductType = Column(String(10))
    TimeInForce = Column(String(10))
    OrderPrice = Column(Float)
    OrderQuantity = Column(Integer)
    OrderStopPrice = Column(Float)
    OrderStatus = Column(String(25))
    OrderDisclosedQuantity = Column(String(10))
    OrderGeneratedDateTime = Column(DateTime)
    CancelRejectReason = Column(String(250))
    GeneratedBy = Column(String(20))
    ExchangeOrderID = Column(String(25))
    OrderUniqueIdentifier = Column(String(30))
    OrderLegStatus = Column(String(20))

