import pickle as pk
from decorator import print_func_text
from functions import escribirlog
import data

class Ticker:
    def __init__(self,**kwargs):
        self.ticker=kwargs.get('ticker')
        self.path=data.pathGan + "tickers.pkl"

    @print_func_text
    def add_ticker(self, params):
        # let's add into a tickers.pkl this ticker
        with open(self.path, "rb") as file:
            t = pk.load(file)
        # now we can add the row
        t[self.ticker] = params
        # save the file again
        with open(self.path, "wb") as file:
            pk.dump(t, file)
        msg = f'{self.ticker} has added into a ticker.pkl file with the parameters {params}'
        escribirlog(msg)

    @print_func_text
    def del_ticker(self):
        # first, open
        with open(self.path, "rb") as file:
            t = pk.load(file)
        # then, delete, but be sure that ticker exists
        try:
            del t[self.ticker]
            msg = f'{self.ticker} was removed from tickers succesfully'
            escribirlog(msg)
        except:
            msg=f'{self.ticker} is not in tickers file '
            escribirlog(msg)
        # finally, save again
        with open(self.path, "wb") as file:
            pk.dump(t, file)


    @print_func_text
    def read_ticker(self):
        msg = "init of read_ticker function"
        escribirlog(msg)
        with open(self.path, "rb") as file:
            t = pk.load(file)
        return t

    @print_func_text
    def get_params(self):
        # the necesaries params are: presicion, qty_presicion, leverage, min_qty, min_money, min_entry
        # well the very first thing is get the leverage
        from functions import cambiarleverage, datosEx
        lvg = cambiarleverage(self.ticker, data.leverage)
        ticker_data = datosEx(self.ticker, lvg)
        rel = data.leverage / lvg
        porcIn = rel * data.porcentajeentrada
        params = {
            'presicion': ticker_data['precision'], 'qty_presicion': ticker_data['presCant'],
            'leverage': lvg, 'min_qty': ticker_data['cantidadMinima'], 'min_money': ticker_data['minimoNot'],
            'min_entry': ticker_data['entrada'],'porcIn':porcIn
        }
        return params

    @print_func_text
    def reinit_ticker(self):
        # if you're testing, this function is very usefull
        t = {}
        with open(self.path, "wb") as file:
            pk.dump(t, file)