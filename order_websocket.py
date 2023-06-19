import json, datetime, logging, traceback
from order_management import handle_order, handle_trade

#The source account which is used to copy trades
from login.userlogin import abcd_i as source_api

from blaze_api.InteractiveSocketClient import OrderSocket_io

file_handler = logging.FileHandler(filename='error.log', mode='a', encoding='utf-8')
logging.basicConfig(handlers=[file_handler], level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s')

client_code = source_api.get_profile()['result']['ClientId']

soc = OrderSocket_io(token = source_api.token, userID = client_code, reconnection_delay_max = 10)

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

def on_connect():
    """Connect from the socket."""
    print('Interactive socket connected successfully!')
    logging.warning('Interactive socket connected successfully!')

def on_message():
    print('I received a message!')
    logging.warning('I received a message!')

def on_joined(data):
    print('Interactive socket joined successfully!' + data)
    logging.warning('Interactive socket joined successfully!' + data)

def on_error(data):
    print('Interactive socket error!' + data)
    logging.warning('Interactive socket error!' + data)

def on_order(data) :
    data = json.loads(data)
    logging.warning(f"Order placed!,{data}")
    print(data)
    if data['ExchangeSegment'] == 'NSEFO':
        error_handler(handle_order,order = data)

def on_trade(data) :
    data = json.loads(data)
    logging.warning(f"Trade Received!, {data}")
    if data['ExchangeSegment'] == 'NSEFO':
        handle_trade(data)


def on_position(data):
    logging.warning("Position Retrieved!" + data)

def on_tradeconversion(data):
    logging.warning("Trade Conversion Received!" + data)

def on_messagelogout(data):
    print("User logged out!" + data)
    logging.warning("User logged out!" + data)

def on_disconnect():
    print('Interactive Socket disconnected!')
    logging.warning('Interactive Socket disconnected!')

soc.on_connect = on_connect
soc.on_message = on_message
soc.on_joined = on_joined
soc.on_error = on_error
soc.on_order = on_order
soc.on_trade = on_trade
soc.on_position = on_position
soc.on_tradeconversion = on_tradeconversion
soc.on_messagelogout = on_messagelogout
soc.on_disconnect = on_disconnect


# Event listener
el = soc.get_emitter()
el.on('connect', on_connect)
el.on('order', on_order)
el.on('trade', on_trade)
el.on('position', on_position)
el.on('tradeConversion', on_tradeconversion)

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
soc.connect()