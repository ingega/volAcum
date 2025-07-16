import pandas as pd

from functions_time import *
import data
from functions import miMail, BinanceAPIException
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
    msg = (f"there's no entry yet, the values are {the_data}, "
           f"gmtime is {time.gmtime()} init section")
    escribirlog(msg)
    # mail just every 4h
    hour = time.gmtime().tm_hour
    minute = time.gmtime().tm_min
    second = time.gmtime().tm_sec
    hour %= 4
    # debug proposes
    print(f"hour, minute, second: {hour}, {minute}, {second}")
    if (hour == data.review_hour
            and minute == data.review_minute
            and second > data.review_second):
        miMail(msg, filename)
    # pause = 60 - data.seconds
    # time.sleep(pause + 1)  # avoid loop


@print_func_text
def make_3bp_entries(entries):
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
        # is time to add the order into a db
        from db import Record
        record = Record()
        # the very first thing, is get the operation_id
        max_id = record.get_max_id()
        if max_id.iloc[0]['max_id']:
            operation_id = max_id.iloc[0]['max_id'] + 1
        else:
            operation_id = 1
        # now we need the commission
        commission = get_trade(tk, e['orderId'])['commission']
        # build the record to be added
        new_record = {
            'strategy': [data.sistema],
            'ticker': [tk],
            'side': [side],
            'quantity': the_order['cantidad'],
            'price': [the_order['precio']],
            'type': ['origin'],
            'commission': [commission],
            'fee': [0],  # is original order
            'epoch_fee': [the_order['epoch']],
            'operation_id': [operation_id],
            'binance_operation_id': [e['orderId']],
            'epoch': [the_order['epoch']],
            'pnl': [0]  # original order doesn't have pnl
        }
        msg = f"the value of the new record is: {new_record}"
        escribirlog(msg)
        # let's add the record
        record.add_record(record=new_record)
        # and then, save for local record
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
            'operation_id': operation_id,
        }
        order = Order(ticker=tk)
        order.add_order(params=params)
        # once set the order and with entry done, let's protect it
        establecerOrdenes(0, tk)


def get_trade(ticker, order_id):
    from main import client
    trades = None
    for i in range(5):
        trades = client.futures_account_trades(symbol=ticker, orderId=order_id)
        if trades:
            break
        time.sleep(1)
    if trades:
        # the operation can get so many trades, so, is necesary summarize
        df = pd.DataFrame(trades)
        df['commission'] = df['commission'].astype('float')
        df['realizedPnl'] = df['realizedPnl'].astype('float')
        commission = df['commission'].sum()
        pnl = df['realizedPnl'].sum()
    else:
        msg = f"the trade info can't get the  commission info"
        escribirlog(msg)
        miMail(msg)
        commission = 0
        pnl = 0
    final = {'commission': commission, 'pnl': pnl}
    return final


def get_fee(ticker, operation_id):
    """
    This function query the last epoch and query with binance
    :param ticker: necessary for client query
    :param operation_id: necessary for db query
    :return: dict with fee values
    """
    from main import client
    # step 1: get the db data
    from db import Record
    record = Record()
    data_record = record.read_record(operation_id=operation_id)
    # data record is a df, so, the last record hace the epoch_fee
    if data_record:
        epoch_fee = data_record[-1]['epoch_fee']
    else:  # this scenario must not exist
        epoch_fee = int(time.time() * 1000)
    # step 2: get binance data
    # function must return last epoch fee
    last_epoch = epoch_fee
    fee = 0
    epoch_fee = int(epoch_fee - 1000)  # 1 sec less just in case
    for i in range(5):  # 5 attempts with 1 sec pause
        trades = client.futures_income_history(
            startTime=epoch_fee, symbol=ticker
        )
        if trades:
            # need accumulation
            for trade in trades:
                if trade['incomeType'] == 'FUNDING_FEE':
                    fee += float(trade['income'])
                    last_epoch = trade['time']
            break
        time.sleep(1)
    final = {
        'fee': fee,
        'epoch_fee': last_epoch
    }
    return final


def main():
    from functions_strategy import init, protect
    n = 0
    while True:
        try:
            init()
            print("just in the main loop")
            while True:  # it's an error prevent
                time.sleep(data.time)  # with this, we can get all
                # the volatility path, also prevent loops between out/in
                every_time(hrs=data.hours, mins=data.minutes, secs=data.seconds)
                # just if we have forbidden hours
                hour = time.gmtime().tm_hour
                if hour < data.forbidden_hour:
                    msg = (f"the {data.forbidden_hour}"
                           f"th hour is not allowed for strategy, "
                           f"the gmtime is {time.asctime(time.gmtime())} ")
                    escribirlog(msg)
                    # inform by mail
                    inform(msg)
                else:
                    # Get the Bars opor
                    print("let's find an opportunity", time.ctime())
                    g = get_all_pairs_opor()
                    df_in = g['df_in']
                    if len(df_in) > 0:
                        msg = (f"We have {len(df_in)} "
                               f"tickers that reach a 3b pattern, "
                               f"those are \n {df_in['ticker']}")
                        escribirlog(msg)
                        miMail(msg)
                        make_3bp_entries(df_in)
                        # protect works until there's no ticker in orders.pkl,
                        # so, when this happens, simply return to time func
                        protect()
                    else:
                        if data.debug_mode:
                            filename = g['path']
                        else:
                            filename = None
                        inform(df_in, filename)
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
            time.sleep(30 + n)
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
