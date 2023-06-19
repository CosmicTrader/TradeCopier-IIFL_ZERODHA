import json, configparser, logging, traceback, time, datetime, pyotp, os, sys
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from kiteconnect import KiteConnect
from blaze_api.Connect import XTSConnect

from files.instruments import download_iifl_instruments, download_kite_instruments

path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)

file_handler = logging.FileHandler(filename='error.log', mode='a', encoding='utf-8')
logging.basicConfig(handlers=[file_handler], level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s')


CFG = configparser.RawConfigParser()
CFG.read('login\\user_credentials.ini')

message_binder = {
    'abcd' : {'iapi' : 'login\\abcd_i.txt', 'mapi' : 'login\\abcd_m.txt'},
    'xyz' : {'iapi' : 'login\\xyz_i.txt'},
    'abc' :{'zapi' : 'login\\abc_z.txt'}
}

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

def get_iapi(user_name):

    try:
        iapi = XTSConnect(apiKey = CFG[user_name]['iapi_key'], secretKey = CFG[user_name]['iapi_secret'], source = "WebAPI")
        
        with open( message_binder[user_name]['iapi'], 'r') as iapi_message:
            iapi_details = json.load(iapi_message)
            iapi_token = iapi_details['result']['token']
            iapi.token = iapi_token
            
            profile = iapi.get_profile()
            if profile['type'] == 'success':
                print(f'Blaze Interactive Session is still valid for {user_name}')
                return iapi
        
    except:
        iapi = XTSConnect(apiKey = CFG[user_name]['iapi_key'], secretKey = CFG[user_name]['iapi_secret'], source = "WebAPI")
        try:
            iapi_details = iapi.interactive_login()
            
            if iapi_details['type'] == 'success':
                with open( message_binder[user_name]['iapi'], 'w') as iapi_message:
                    iapi_message.write(json.dumps(iapi_details))
                print(f'New Interactive Login Completed for {user_name}')
            
                return iapi
        except Exception as e:
            print(f'Error occurred while trying to interactive log in for user {user_name} : {e}')

def get_mapi(user_name):
    
    try:
        with open( message_binder[user_name]['mapi'], 'r') as mapi_message:
            mapi = XTSConnect(apiKey = CFG[user_name]['mapi_key'], secretKey = CFG[user_name]['mapi_secret'], source = "WebAPI")
            mapi_details = json.load(mapi_message)
            mapi_token = mapi_details['result']['token']
            mapi.token = mapi_token
        
            client_config = mapi.get_config()
            if client_config['type'] == 'success':
                print(f'Blaze Market Session is still valid for {user_name}')
                return mapi
            else:
                raise Exception
        
    except:
        mapi = XTSConnect(apiKey = CFG[user_name]['mapi_key'], secretKey = CFG[user_name]['mapi_secret'], source = "WebAPI")
        try:
            mapi_details = mapi.marketdata_login()
            if mapi_details['type'] == 'success':
                with open( message_binder[user_name]['mapi'], 'w') as mapi_message:
                    mapi_message.write(json.dumps(mapi_details))
                print(f'New Market API Login Completed for {user_name}')

                #download instrument files for iifl. #change name below 
                if user_name == 'abcd':
                    download_iifl_instruments(iifl_market_api= mapi)

                return mapi
        except Exception as e:
            print(f'Error occurred while trying to market log in for user {user_name} : {e}')

def kite_login(kite, user_name):

    options = Options()
    options.add_argument('--headless')

    service = Service('chromedriver.exe')
    driver = webdriver.Chrome(service=service, options= options)
    driver.get(kite.login_url())

    login = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@id='container']")))

    login.find_element(By.XPATH, "//input[@type='text']").send_keys(CFG[user_name]['zuser_id'])
    login.find_element(By.XPATH, "//input[@type='password']").send_keys(CFG[user_name]['zuser_password'])
    login.find_element(By.XPATH, "//button[@type='submit']").click()

    time.sleep(2)
    otp = pyotp.TOTP(CFG[user_name]['ztotp']).now()
    login.find_element(By.XPATH, "//input[@type='text']").send_keys(otp)

    time.sleep(2)
    response = driver.current_url
    print(response)
    request_token = response.split('request_token=')[1].split('&')[0]
    data = kite.generate_session(request_token = request_token, api_secret=CFG[user_name]['zapi_secret'])
    
    return data

def get_zapi(user_name):
    zapi = KiteConnect(api_key = CFG[user_name]['zapi_key'])

    try:
        with open(message_binder[user_name]['zapi'], 'r') as zapi_message:
            zapi_details = json.load(zapi_message)
            zapi_token = zapi_details['access_token']
            zapi.access_token = zapi_token
            profile = zapi.profile()
            print(f'Kite Session is still valid for {user_name}')
            return zapi
    except:
        zapi = KiteConnect(api_key = CFG[user_name]['zapi_key'])
        try:
            zapi_details = kite_login(zapi, user_name)
            profile = zapi.profile()
            with open( message_binder[user_name]['zapi'], 'w') as zapi_message:
                zapi_details['login_time'] = datetime.datetime.strftime(zapi_details['login_time'], '%Y-%m-%d %H:%M:%S')
                zapi_message.write(json.dumps(zapi_details))
                print(f'New Zerodha Login Completed for {user_name}')
            
            #download instrument files for kite. #change name below 
            if user_name == 'abc':
                download_kite_instruments(zerodha_api = zapi)

            return zapi
        
        except Exception as e:
            print(f'Error occurred while trying to zerodha log in for user {user_name} : {e}')


abcd_i = error_handler(get_iapi, user_name = 'abcd')
abcd_m = error_handler(get_mapi, user_name = 'abcd')

abc_z = error_handler(get_iapi, user_name = 'abc')
xyz_i = error_handler(get_zapi, user_name = 'xyz')