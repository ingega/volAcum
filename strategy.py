import time

from functions_time import *
import data
from functions_strategy import miMail, BinanceAPIException
from functions_files import escribirlog
import requests
from main import get_all_pairs_opor
from decorators import print_func_text
from tickers import Ticker
from orders import Order

path = data.path

@print_func_text
def inform(the_data, filename=None):  # to inform about the values in entries, and every 4hrs send a mail
    # inform
    msg = f"there's no entry yet, the values are {the_data}, gmtime is {time.gmtime()}"
    if validate_hours():
        escribirlog(msg)
        miMail(msg,filename)
        pause = 60 - data.seconds
        time.sleep(pause + 1)  # avoid loop
    else:
        print(msg)

@print_func_text
def make_entries(entries):
    # ok the very first step, the importations
    from functions_strategy import establecerOrdenes, getEntry, checarOrden
    for p in range(len(entries)):
        # the step two of strategy, is make a loop for every ticker inside
        # every ticker was added by the function add_ticker from class Ticker
        tk = entries.iloc[p]['ticker']
        ticker = Ticker(ticker=tk)
        params = ticker.get_params()
        ticker.add_ticker(params)
        side = entries.iloc[0]['side']
        # time to make entry
        e = getEntry(tk, side)
        time.sleep(10)  # to make query
        the_order = checarOrden(tk, e['orderId'])
        params = {
            'priceIn': the_order['precio'],
            'priceOut': 0,
            'originalPrice': the_order['precio'],
            'side': side,
            'dateIn': time.time(),
            'dateOut': 0,
            'qty': the_order['cantidad'],
            'orderA': e['orderId'],
            'orderSL': 0,
            'orderTP': 0,
            'adjust': 0,
            'orderBUY': 0,
            'orderSELL': 0,
            'epochIn': 0,
        }
        order = Order(ticker=tk)
        order.add_order(params=params)
        # once seted the order and with entry done, let's protect it
        establecerOrdenes(0, tk)

def validate_hours():
    hours = time.gmtime().tm_hour
    hours %= 4 # every 4 hours
    minutes = time.gmtime().tm_min
    if hours == 3 and minutes == 59:
        return True
    else:
        return False

def main():
    from functions_strategy import init, protect
    n = 0
    while True:
        try:
            init()
            print("just in the principal loop")
            while True: # it's an error prevent
                time.sleep(data.time)  # with this, we can get all the volatibility path, also prevent loops between out/in
                every_time(hours=data.hours,mins=data.minutes,secs=data.seconds)
                # this strategy only works in american sc
                hour=time.gmtime().tm_hour
                if hour < data.forbidden_hour:
                    # due to this strategy search every minute, we need to validate the hour
                    if validate_hours():
                        msg=f"the {data.forbidden_hour}th hour is not allowed for strategy, the gmtime is {time.asctime(time.gmtime())} "
                        escribirlog(msg)
                        miMail(msg)
                else:
                    # Get the Bars opor
                    g = get_all_pairs_opor()
                    df_in=g['df_in']
                    if len(df_in) > 0:
                        msg = f"We have {len(df_in)} tickers that reach the volume threeshold, those are \n {df_in['ticker']}"
                        escribirlog(msg)
                        miMail(msg)
                        make_entries(df_in)
                        # protect works until there's no ticker in orders.pkl, so, when this happen, simply return to time func
                        protect()
                    else:
                        if data.debug_mode:
                            filename=g['path']
                        else:
                            filename=None
                        inform(df_in,filename)
        except BinanceAPIException as error:
            if error.code == -1021:  # timestamp, let's check booth
                from functions import cliente
                msg = f"timestamp it's ahead more than 1000 ms, the ts of binance is {cliente.futures_time()}"
                msg += f" and ts of computer is {time.time()}"
                escribirlog(msg)
            elif error.code == -1008:  # server overloaded, let's sleep 10 scs
                time.sleep(10)
            else:
                msj = f"a binance error are commited\n"
                msj += f'{error.message} number {error.code}'
                escribirlog(msj)
                miMail(msj)
            n += 1
            # le damos 30 sgs
            time.sleep(30+n)
        except requests.exceptions.ConnectionError as err:
            # Handle the "Connection aborted" error separately
            msg = f"Connection aborted error: {err}"
            escribirlog(msg)
            time.sleep(0.2)  # Wait for 200 a while before retrying
        except Exception as error:
            # Handle other exceptions here
            print(f"Another error: {type(error).__name__}: {str(error)}")
            n += 1
            if n > 10:
                msg = "there's more than 10 errors, must check by human"
                escribirlog(msg)
                miMail(msg)
                n = 0

if __name__ == '__main__':
    main()
