import logging, traceback, datetime, time
import pandas as pd

#Target accounts which are used for copying trades.
from login.userlogin import abc_z, xyz_i

from api_func import ( iifl_place_order, iifl_modify_order, iifl_cancel_order, iifl_get_order_history, iifl_get_orders,
                      kite_place_order, kite_modify_order, kite_cancel_order, kite_order_history,
                      read_json_file, update_json_file, send_order_error_message )

from db_utils import save_parent_account_order


file_handler = logging.FileHandler(filename='error.log', mode='a', encoding='utf-8')
logging.basicConfig(handlers=[file_handler], level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s')

# Please make sure to update following file regularly
max_qty_df = pd.read_excel('qtyfreeze.xls', index_col=0)
max_qty_df.rename(columns = {col : col.strip() for col in max_qty_df.columns}, inplace = True)
max_qty_df.SYMBOL = max_qty_df.SYMBOL.str.strip()

kite_instruments = pd.read_csv(r'files\kite_fno.csv')
parent_child_account_order_mapper = read_json_file('order_mapper')

#add all user objects in list below according to the broker.
iifl_accounts    = [xyz_i]
zerodha_accounts = [abc_z]

#Add all user objects in the dict below and map them with proper account name and broker code.
account_name_mapper = {
    abc_z : 'abc_kite',
    xyz_i : 'xyz_iifl'
}

#order multiplier dictionary
#After multipying order_multiplier with order quantity, if order size is less than one lot, no order will be placed for that user
order_multiplier_mapper = {
    abc_z : 1,
    xyz_i : 2,
}

kite_variable_mapper = {
    'Market'     : "MARKET",
    'Limit'      : "LIMIT",
    'StopMarket' : "SL-M",
    'StopLimit'  : "SL"
}

def error_handler(func, *args, **kwargs):
    # wrapper function for handling errors
    try:
        return func(*args, **kwargs)
    except Exception as e:
        #assign exception to the error_type
        print(f'ERROR IN {func} @ {datetime.datetime.now().time().replace(microsecond=0)} : {e}')
        logging.error(f'ERROR IN {func} : {e}')
        logging.error(f'FUNCTION ARGUMENTS ARE :{args}, {kwargs}')
        logging.error(traceback.format_exc())
        return


def handle_new_order(order) :
    global parent_child_account_order_mapper
    global kite_instruments, max_qty_df
    parent_child_account_order_mapper [str(order['AppOrderID'])] = {}
    error_orders = []

    symbol_kite_token   = kite_instruments.loc[kite_instruments['exchange_token'] == order['ExchangeInstrumentID']].iloc[0]
    kite_trading_symbol = symbol_kite_token['tradingsymbol']
    lot_size            = symbol_kite_token['lot_size']
    try:
        symbol_max_qty = max_qty_df[max_qty_df.SYMBOL == symbol_kite_token['tradingsymbol']].iloc[0]
    except:
        symbol_max_qty = 300

    for user_api in zerodha_accounts :
        
        try:
            order_multiplier = order_multiplier_mapper[user_api]
        except Exception as e:
            print('Please Ensure that account is added in order_multiplier_mapper dictionary')
            order_multiplier = 1

        number_of_lot = int(int(order['OrderQuantity']) / lot_size * order_multiplier)
        totalQuantity = number_of_lot * lot_size
        _orders = []

        while totalQuantity > 0:
            if totalQuantity > symbol_max_qty:
                orderQuantity = symbol_max_qty
                totalQuantity -= orderQuantity
            else:
                orderQuantity = totalQuantity
                totalQuantity = totalQuantity - orderQuantity

            new_kite_order = error_handler( kite_place_order, zapi = user_api, variety = 'regular', exchange = 'NFO', 
                                tradingsymbol = kite_trading_symbol, transaction_type = str(order['OrderSide']).upper(), quantity = orderQuantity,
                                product = 'MIS', order_type = kite_variable_mapper [order['OrderType']], price = order['OrderPrice'], 
                                validity = 'DAY', trigger_price = order['OrderStopPrice'], tag = order['AppOrderID'], disclosed_quantity = 0 )
            
            if new_kite_order:
                _orders.append(new_kite_order)
            else:
                message = f'Sourece: "New Order". Error while Placing New order for user {account_name_mapper[user_api]}. Source Order : {order}'
                logging.critical(message)
                error_orders.append((account_name_mapper[user_api], order))
        
        parent_child_account_order_mapper [str(order['AppOrderID'])] [account_name_mapper[user_api]] = _orders

    for user_api in iifl_accounts :
        
        try:
            order_multiplier = order_multiplier_mapper[user_api]
        except Exception as e:
            print('Please Ensure that account is added in order_multiplier_mapper dictionary')
            order_multiplier = 1
        
        number_of_lot = int(int(order['OrderQuantity']) / lot_size * order_multiplier)
        totalQuantity = number_of_lot * lot_size
        _orders = []
        while totalQuantity > 0:
            if totalQuantity > symbol_max_qty:
                orderQuantity = symbol_max_qty
                totalQuantity -= orderQuantity
            else:
                orderQuantity = totalQuantity
                totalQuantity = totalQuantity - orderQuantity
            
            new_iifl_order = error_handler( iifl_place_order, iapi = user_api, exchangeSegment = 'NSEFO', exchangeInstrumentID = order['ExchangeInstrumentID'],
                            productType = order['ProductType'], orderType = order['OrderType'], orderSide = order['OrderSide'], timeInForce = order['TimeInForce'],
                            disclosedQuantity = 0, orderQuantity = orderQuantity,
                            limitPrice = order['OrderPrice'], stopPrice = order['OrderStopPrice'], 
                            orderUniqueIdentifier = order['AppOrderID'], clientID = order['ClientID'] )
            
            if new_iifl_order :
                _orders.append(new_iifl_order['result']['AppOrderID'])
            else :
                error_orders.append((account_name_mapper[user_api], order))
    
        parent_child_account_order_mapper [str(order['AppOrderID'])] [account_name_mapper[user_api]] = _orders
    
    update_json_file('order_mapper', parent_child_account_order_mapper)

    return parent_child_account_order_mapper [str(order['AppOrderID'])], error_orders

def handle_modified_order(order) :
    global kite_instruments, parent_child_account_order_mapper
    
    lot_size = kite_instruments.loc[kite_instruments.exchange_token == order['ExchangeInstrumentID']].iloc[0]['lot_size']

    error_orders = []

    for user_api in iifl_accounts :
        try:
            try:
                order_multiplier = order_multiplier_mapper[user_api]
            except Exception as e:
                print('Please Ensure that account is added in order_multiplier_mapper dictionary')
                order_multiplier = 1
        
            for iiflOrderID in parent_child_account_order_mapper [str(order['AppOrderID'])] [account_name_mapper[user_api]] :
                number_of_lot = round(int(order['OrderQuantity'])  / lot_size * order_multiplier)
                orderQuantity = number_of_lot * lot_size

                if orderQuantity > 0:
                    modified_iifl_order = iifl_modify_order(iapi = user_api, appOrderID = iiflOrderID, modifiedProductType = order['ProductType'], modifiedOrderType = order['OrderType'],
                                    modifiedOrderQuantity = orderQuantity, modifiedDisclosedQuantity = 0, modifiedTimeInForce = order['TimeInForce'], 
                                    modifiedLimitPrice = order['OrderPrice'], modifiedStopPrice = order['OrderStopPrice'], orderUniqueIdentifier = order['AppOrderID']
                                    )
                
                # change this order mapping here as we are mapping it with original orders and not modified one
                if not modified_iifl_order :
                    error_orders.append((user_api, order))
        except KeyError as e:
            print('error while modifying order',e)
            logging.error(f'error in modifying order : {e}')
            logging.error(traceback.format_exc())
            

    for user_api in zerodha_accounts :
        try:
            try:
                order_multiplier = order_multiplier_mapper[user_api]
            except Exception as e:
                print('Please Ensure that account is added in order_multiplier_mapper dictionary')
                order_multiplier = 1

            for kiteOrderID in parent_child_account_order_mapper [str(order['AppOrderID'])] [account_name_mapper[user_api]] :
                number_of_lot = round(int(order['OrderQuantity'])  / lot_size * order_multiplier)
                orderQuantity = number_of_lot * lot_size
                
                if orderQuantity > 0 :
                    modified_kite_order = error_handler(kite_modify_order, zapi= user_api, variety = 'regular', order_id = kiteOrderID, quantity = orderQuantity, price = order['OrderPrice'], 
                                        order_type = kite_variable_mapper [order['OrderType']], trigger_price = order['OrderStopPrice'], 
                                        validity = 'DAY', disclosed_quantity = 0)

                    if not modified_kite_order:
                        error_orders.append((user_api, order))
        except KeyError as e:
            print('error while modifying order',e)
            logging.error(f'error in modifying order : {e}')
            logging.error(traceback.format_exc())

    return error_orders

def handle_cancelled_order(order):
    global parent_child_account_order_mapper
    error_orders = []

    for user_api in iifl_accounts :
        try:
            for appOrderID in parent_child_account_order_mapper [str(order['AppOrderID'])] [account_name_mapper[user_api]] : 
                cancelled_order = error_handler(iifl_cancel_order, iapi = user_api, appOrderID = appOrderID, orderUniqueIdentifier = order['AppOrderID'])
        except Exception as e:
            print(e)
            logging.error(f'error in cancelling order : {e}')
            logging.error(traceback.format_exc())

    for user_api in zerodha_accounts :
        try:
            for appOrderID in parent_child_account_order_mapper [str(order['AppOrderID'])] [account_name_mapper[user_api]] :
                cancelled_order = error_handler(kite_cancel_order, zapi = user_api, order_id = appOrderID, variety = 'regular')
        except Exception as e:
            logging.error(f'error in cancelling order : {e}')
            logging.error(traceback.format_exc())

    return error_orders


def check_order_status(new_orders):

    rejected_orders = []

    for value in new_orders:
        key = next(filter(lambda k: account_name_mapper[k] == value, account_name_mapper.keys()), None)

        if 'kite' in value:
            for ord in new_orders[value]:
                res = error_handler(kite_order_history, key, ord)

                if res['status'] == 'REJECTED':
                    rejected_orders.append(res)
                    
                else:
                    print(res['status'])

        elif 'iifl' in value:
            for ord in new_orders[value]:
                res = error_handler(iifl_get_order_history, key, ord)

                if res['result'][-1]['OrderStatus'] == 'Rejected':
                    rejected_orders.append(res['result'])
                    
                else:
                    print(res['result'][-1]['OrderStatus'])

    return rejected_orders


def handle_order(order):

    global parent_child_account_order_mapper

    if order['OrderStatus'] == 'New':
        if str(order['AppOrderID']) not in parent_child_account_order_mapper:
            new_orders, error_orders = error_handler(handle_new_order, order = order)
            rejected_orders = check_order_status(new_orders)
            save_parent_account_order(order)
            
            for order in rejected_orders:
                message = f'Sourece: "New Order". Order Rejected while Placing New order for user {order[0]}. Source Order : {order[1]}'
                error_handler(send_order_error_message, message=message)
            
            for order in error_orders:
                message = f'Sourece: "New Order". Error while Placing New order for user {order[0]}. Source Order : {order[1]}'
                error_handler(send_order_error_message, message=message)
            
    elif order['OrderStatus'] == 'Replaced':
        error_orders = error_handler(handle_modified_order, order = order)
        save_parent_account_order(order)
        
        for order in error_orders:
            message = f'Sourece: "Modified Order". Error while Modifying order for user {order[0]}. Source Order : {order[1]}'
            error_handler(send_order_error_message, message=message)
        

    elif order['OrderStatus'] == 'Cancelled':
        error_orders = error_handler(handle_cancelled_order, order = order)
        save_parent_account_order(order)

        for order in error_orders:
            message = f'Sourece: "Cancelled Order". Error while Cancelling order for user {order[0]}. Source Order : {order[1]}'
            error_handler(send_order_error_message, message=message)
        
    return

def handle_trade(trade):
    time.sleep(3)
    error_orders = []
    trade_orders = parent_child_account_order_mapper[trade['AppOrderID']]
    
    for order in trade_orders:
        user_api = next(filter(lambda k: account_name_mapper[k] == order, account_name_mapper.keys()), None)

        if 'kite' in order:
            for ord in trade_orders[order]:
                res = kite_order_history(user_api, ord)
                if res['order_status'] not in ['COMPLETE', 'CANCELLED']:
                    modified_order = error_handler(kite_modify_order, zapi = user_api, order_id = ord, order_type = 'MARKET', variety='regular')
                    if not modified_order:
                        error_orders.append(account_name_mapper[user_api], res)

        elif 'iifl' in order:
            for ord in trade_orders[order]:
                res = iifl_get_order_history(user_api, ord)['result'][-1]
                if res['OrderStatus'] not in ['Filled', 'Cancelled']  :
                    modified_order = error_handler(iifl_modify_order, iapi = user_api, appOrderID = ord, modifiedOrderType = 'Market',
                                                   modifiedProductType = res['ProductType'], modifiedOrderQuantity = res['OrderQuantity'], 
                                                   modifiedDisclosedQuantity = 0, modifiedTimeInForce = res['TimeInForce'], modifiedLimitPrice = 0, 
                                                   modifiedStopPrice = res['OrderStopPrice'], orderUniqueIdentifier = res['AppOrderID'] )
                    if not modified_order:
                        error_orders.append(account_name_mapper[user_api], res)
    
    for order in error_orders:
        message = f'Sourece: "Trade Endpoint". Error while modifying order for user {order[0]}. Source Trade : {order[1]}'
        send_order_error_message(message=message)