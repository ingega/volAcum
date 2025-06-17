import pickle as pk
from decorators import print_func_text
from functions_files import escribirlog
from data import leverage, porcentajeentrada, path


class Ticker:
    """
    Instructions to add a ticker:
    get an instance of ticker with ticker='TICKER'
    then make params = ticker.get_params()
    finally ticker.add_ticker(params)
    use raw Ticker for read all dict
    """
    def __init__(self, **kwargs):
        self.ticker = kwargs.get('ticker')
        self.my_path = path / "tickers.pkl"

    @print_func_text
    def add_ticker(self, params):
        # let's add into a tickers.pkl this ticker
        with open(self.my_path, "rb") as file:
            t = pk.load(file)
        # now we can add the row
        t[self.ticker] = params
        # save the file again
        with open(self.my_path, "wb") as file:
            pk.dump(t, file)
        msg = f'{self.ticker} has added into a ticker.pkl file with the parameters {params}'
        escribirlog(msg)

    @print_func_text
    def del_ticker(self):
        # first, open
        with open(self.my_path, "rb") as file:
            t = pk.load(file)
        # then, delete, but be sure that ticker exists
        try:
            del t[self.ticker]
            msg = f'{self.ticker} was removed from tickers successfully'
            escribirlog(msg)
        except Exception as _:
            msg = f'{self.ticker} is not in tickers file '
            escribirlog(msg)
        # finally, save again
        with open(self.my_path, "wb") as file:
            pk.dump(t, file)

    @print_func_text
    def read_ticker(self):
        msg = "init of read_ticker function"
        escribirlog(msg)
        with open(self.my_path, "rb") as file:
            t = pk.load(file)
        return t

    @print_func_text
    def get_params(self):
        # the necessary params are: precision, qty precision, leverage,
        # min_qty, min_money, min_entry
        # well the very first thing is get the leverage
        from functions import cambiarleverage, datosEx
        lvg = cambiarleverage(self.ticker, leverage)
        ticker_data = datosEx(self.ticker, lvg)
        rel = leverage / lvg
        porcIn = rel * porcentajeentrada
        params = {
            'name': self.ticker, 'presicion': ticker_data['precision'],
            'qty_presicion': ticker_data['presCant'], 'leverage': lvg,
            'min_qty': ticker_data['cantidadMinima'],
            'min_money': ticker_data['minimoNot'],
            'min_entry': ticker_data['entrada'], 'porcIn': porcIn
        }
        return params

    @print_func_text
    def reinit_ticker(self):
        # if you're testing, this function is very usefull
        t = {}
        with open(self.my_path, "wb") as file:
            pk.dump(t, file)


def main():
    pass


if __name__ == '__init__':
    main()
