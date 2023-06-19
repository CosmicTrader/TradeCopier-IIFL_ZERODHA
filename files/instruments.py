import os, sys, logging, traceback, datetime
import pandas as pd

path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)

file_handler = logging.FileHandler(filename='error.log', mode='a', encoding='utf-8')
logging.basicConfig(handlers=[file_handler], level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s')

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

def download_iifl_instruments(iifl_market_api):

    os.chdir('files')
    nse = iifl_market_api.get_master(['NSECM'])
    fno = iifl_market_api.get_master(['NSEFO'])

    with open('iifl_nse.txt', 'w') as file:
        file.write('ExchangeSegment|ExchangeInstrumentID|InstrumentType|Name|Description|Series|NameWithSeries|InstrumentID|PriceBand.High|PriceBand.Low|FreezeQty|TickSize|LotSize|Multiplier'+'\n'+nse['result'])

    with open('iifl_fno.txt', 'w') as file:
        file.write('ExchangeSegment|ExchangeInstrumentID|InstrumentType|Name|Description|Series|NameWithSeries|InstrumentID|PriceBand.High|PriceBand.Low|FreezeQty|TickSize|LotSize|Multiplier|UnderlyingInstrumentId|UnderlyingIndexName|ContractExpiration|StrikePrice|OptionType'+'\n'+fno['result'])

    os.chdir('..')
    return

def download_kite_instruments(zerodha_api):

    os.chdir('files')

    pd.DataFrame(zerodha_api.instruments('NSE')).to_csv('kite_nse.csv', index = False)
    pd.DataFrame(zerodha_api.instruments('NFO')).to_csv('kite_fno.csv', index = False)

    os.chdir('..')
    return
