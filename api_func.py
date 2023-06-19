import json, requests, logging

file_handler = logging.FileHandler(filename='error.log', mode='a', encoding='utf-8')
logging.basicConfig(handlers=[file_handler], level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s')

chat_id = ''
telegram_bot_token = ''

def send_order_error_message(message='hi', current_try = 1):
    try:
        response = requests.get(f'https://api.telegram.org/bot{telegram_bot_token}/sendMessage?chat_id={chat_id}&text={message}')
        return response
    except Exception as e:
        
        if type(e) == requests.exceptions.ConnectionError and current_try < 5:
            current_try += 1
            send_order_error_message(message=message, current_try=current_try)
        else:
            print('Error while sending Telegram Message',e)
            logging.error(f'Error while sending Telegram Message : {e}')

def update_json_file(file_name, data):
    with open(file_name+".json", "w") as outfile:
        json.dump(data, outfile)
    return

def read_json_file(file_name):
    with open(file_name+".json", "r+") as file:
        data = json.load(file)
        return data

def iifl_place_order(iapi, exchangeSegment, exchangeInstrumentID, productType, orderType, orderSide, timeInForce,
                disclosedQuantity, orderQuantity, limitPrice, stopPrice, orderUniqueIdentifier, clientID=None ):
    
    return iapi.place_order(exchangeSegment = str(exchangeSegment), exchangeInstrumentID = int(exchangeInstrumentID), productType = str(productType), 
                            orderType= str(orderType), orderSide= str(orderSide), timeInForce= str(timeInForce), disclosedQuantity= int(disclosedQuantity),
                            orderQuantity= str(orderQuantity), limitPrice= float(limitPrice), stopPrice= float(stopPrice), 
                            orderUniqueIdentifier= str(orderUniqueIdentifier), clientID= str(clientID))

def iifl_modify_order(iapi, appOrderID, modifiedProductType, modifiedOrderType,modifiedOrderQuantity,
                      modifiedDisclosedQuantity,modifiedLimitPrice,modifiedStopPrice,modifiedTimeInForce,
                      orderUniqueIdentifier,clientID=None):
    
    """The facility to modify your open orders by allowing you to change limit order to market or vice versa,
    change Price or Quantity of the limit open order, change disclosed quantity or stop-loss of any
    open stop loss order. """

    return iapi.modify_order(appOrderID = int(appOrderID), modifiedProductType = str(modifiedProductType), modifiedOrderType = str(modifiedOrderType),                            
                            modifiedOrderQuantity = int(modifiedOrderQuantity), modifiedDisclosedQuantity = int(modifiedDisclosedQuantity),
                            modifiedLimitPrice = float(modifiedLimitPrice), modifiedStopPrice = float(modifiedStopPrice), 
                            modifiedTimeInForce = str(modifiedTimeInForce), orderUniqueIdentifier = str(orderUniqueIdentifier), clientID = str(clientID))

def iifl_cancel_order(iapi, appOrderID, orderUniqueIdentifier, clientID=None):
    
    """This API can be called to cancel any open order of the user by providing correct appOrderID matching with
    the chosen open order to cancel. """
    
    return iapi.cancel_order(appOrderID = appOrderID, orderUniqueIdentifier = orderUniqueIdentifier, clientID = clientID)

def iifl_cancelall_order(iapi, exchangeSegment, exchangeInstrumentID):
    
    """This API can be called to cancel all open order of the user by providing exchange segment and exchange instrument ID """
    
    return iapi.cancelall_order(exchangeSegment = exchangeSegment, exchangeInstrumentID = exchangeInstrumentID)

def iifl_get_orders(iapi, clientID = None):

    return iapi.get_order_book(clientID = clientID)['result']

def iifl_get_trades(iapi, clientID = None):
    
    """Trade book returns a list of all trades executed on a particular day , that were placed by the user . The
    trade book will display all filled and partially filled orders. """
    
    return iapi.get_trade(clientID = clientID)

def iifl_get_profile(iapi, clientID=None):

    return iapi.get_profile(clientID = clientID)

def iifl_get_balance(iapi, clientID = None):

    return iapi.get_balance(clientID = clientID)

def iifl_get_order_history(iapi, appOrderID, clientID=None):
    
    """Order history will provide particular order trail chain. This indicate the particular order & its state
    changes. i.e.Pending New to New, New to PartiallyFilled & PartiallyFilled to Filled etc """
    
    return iapi.get_order_history(appOrderID=appOrderID, clientID=clientID)

def iifl_get_positions_daywise(iapi, clientID=None):
    
    """The positions API returns positions by day, which is a snapshot of the buying and selling activity for
    that particular day."""

    return iapi.get_position_netwise(clientID = clientID)
    
def iifl_get_positions_netwise(iapi, clientID=None):
    
    """The positions API positions by net. Net is the actual, current net position portfolio."""
    
    return iapi.get_position_netwise(clientID = clientID)

def iifl_convert_position(iapi, exchangeSegment, exchangeInstrumentID, targetQty, isDayWise, oldProductType,
                        newProductType, clientID=None):
    
    """Convert position API, enable users to convert their open positions from NRML intra-day to Short term MIS or
    vice versa, provided that there is sufficient margin or funds in the account to effect such conversion """
    
    return iapi.convert_position(exchangeSegment = exchangeSegment,exchangeInstrumentID = exchangeInstrumentID, 
                                 targetQty = targetQty, isDayWise = isDayWise,oldProductType = oldProductType,
                                 newProductType = newProductType, clientID = clientID)

def iifl_get_quotes(mapi, Instruments, xtsMessageCode = 1501, publishFormat = 'JSON'):
    
    return mapi.get_quote(Instruments = Instruments, xtsMessageCode = xtsMessageCode, publishFormat = publishFormat)



def kite_place_order(zapi, exchange : str, tradingsymbol : str, transaction_type : str, order_type : str, variety : str = 'regular', product : str = 'MIS', 
                    quantity : int = 1, disclosed_quantity : int = None, price : float = 0, trigger_price : float = None,
                    validity_ttl = None, validity : str = None, tag : str = None): 
    
    return zapi.place_order(variety = str(variety), exchange = str(exchange), tradingsymbol = str(tradingsymbol), transaction_type = str(transaction_type),
                                quantity = int(quantity), product = str(product), order_type = str(order_type), price = float(price), validity = str(validity),
                                disclosed_quantity = int(disclosed_quantity), trigger_price = float(trigger_price), tag = str(tag))

def kite_modify_order( zapi, variety, order_id, parent_order_id = None, quantity = None, price = None, 
                      order_type = None, trigger_price = None, validity = None, disclosed_quantity = None):

    return zapi.modify_order(validity = validity, variety = variety, order_id = order_id, parent_order_id = parent_order_id, price = price, 
                             quantity = quantity, order_type = order_type, trigger_price = trigger_price, disclosed_quantity = disclosed_quantity)

def kite_cancel_order(zapi, order_id, variety = 'regular', parent_order_id=None):
    
    return zapi.cancel_order(variety = variety, order_id = order_id, parent_order_id = parent_order_id)

def kite_ltp(zapi, instruments):

    return zapi.ltp(instruments = instruments)

def kite_get_quote(zapi, instruments):
    '''
    instruments is a list of instruments, Instrument are in the format of exchange:tradingsymbol. For example NSE:INFY
    '''
    return zapi.quote(instruments = instruments)

def kite_order_history(zapi, order_id):

    return zapi.order_history(order_id = order_id)[-1]

def kite_get_orders(zapi):

    return zapi.orders()

def kite_get_positions(zapi):

    return zapi.positions()

def kite_get_trades(zapi):

    return zapi.trades()
