import logging, traceback, configparser, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Base, Parent_Order

logger = logging.getLogger(__name__)


CFG = configparser.RawConfigParser()
CFG.read('db_config.ini')

#database username and password variables.
DB_USERNAME = CFG['db_credentials']['db_username']
DB_PASSWORD =  CFG['db_credentials']['db_password']

#other database variables.
DB_HOST = CFG['db_credentials']['db_host']
DB_PORT = CFG['db_credentials']['db_port']
DB_NAME = CFG['db_credentials']['db_name']

DB = 'mysql'
DB_CONNECTOR = 'mysqlconnector'

#database connection URL
DB_URL = f"{ DB }+{ DB_CONNECTOR }://{ DB_USERNAME }:{ DB_PASSWORD }@{ DB_HOST }:{ DB_PORT }/{ DB_NAME }"

Engine = create_engine(DB_URL)

#get all the user credentials and database credentials from congif.ini file
Base.metadata.create_all(Engine)

def error_handler(func, *args, **kwargs):
    # wrapper function for handling errors
    try:
        return func(*args, **kwargs)
    except Exception as e:
        #assign exception to the error_type
        print(f'ERROR IN {func} @ {datetime.datetime.now().time().replace(microsecond=0)} : {e}')
        logging.error(f'ERROR IN {func} @ {datetime.datetime.now().time().replace(microsecond=0)} : {e}')
        logging.error(f'FUNCTION ARGUMENTS ARE :{args}, {kwargs}')
        logging.error(traceback.format_exc())
        return

def save_parent_account_order(order):
    
    keep_keys = ['ClientID','AppOrderID','TradingSymbol','OrderCategoryType','ExchangeSegment','ExchangeInstrumentID','OrderSide',
                'OrderType','ProductType','TimeInForce','OrderPrice','OrderQuantity','OrderStopPrice','OrderStatus','OrderDisclosedQuantity',
                'OrderGeneratedDateTime','CancelRejectReason','GeneratedBy','ExchangeOrderID','OrderUniqueIdentifier','OrderLegStatus']
    m_order = {}
    for key in order:
        if key in keep_keys:
            m_order[key] = order[key]

    mapper_order = Parent_Order(**m_order)

    with Session(Engine) as session:
        session.add(mapper_order) #add error in the database
        session.commit() #save changes made in database
