from functions import escribirlog
import data
from decorator import print_func_text
import pickle as pk

class Order:
    def __init__(self,**kwargs):
        self.ticker=kwargs.get('ticker')
        self.path=data.pathGan + "orders.pkl"

    @print_func_text
    def add_order(self, params):
        # let's add into a tickers.pkl this ticker
        with open(self.path, "rb") as file:
            o = pk.load(file)
        # now we can add the row
        o[self.ticker] = params
        # save the file again
        with open(self.path, "wb") as file:
            pk.dump(o, file)
        msg = f'{self.ticker} order has added into a order.pkl file with the parameters {params}'
        escribirlog(msg)

    @print_func_text
    def del_order(self):
        # first, open
        with open(self.path, "rb") as file:
            o = pk.load(file)
        # then, delete, but be sure that ticker exists
        try:
            del o[self.ticker]
            msg=f'{self.ticker} was removed from orders succesfully'
            escribirlog(msg)
        except:
            msg=f'{self.ticker} is not in orders file '
            escribirlog(msg)
        # finally, save again
        with open(self.path, "wb") as file:
            pk.dump(o, file)

    def read_order(self):
        with open(self.path, "rb") as file:
            o = pk.load(file)
        return o

    @print_func_text
    def update_order(self,params=None,entire=False,**parameters):
        # ok in this case, params is used for change all parameters, but set entire to True
        # if only need change some parameter, use **parameters
        o={}
        with open(self.path, "rb") as file:
            o = pk.load(file)
        # Update all parameters at once
        if entire:
            if params is not None:
                o[self.ticker] = params
            else:
                raise ValueError("entire is seted to True, so 'params' must be provided.")
        else:
            # Update only specified parameters
            if self.ticker not in o:
                raise KeyError(f"Ticker '{self.ticker}' not found in orders.")

            for name_of_parameter, value_of_parameter in parameters.items():
                o[self.ticker][name_of_parameter] = value_of_parameter
                msg=f'{name_of_parameter} has been stablished in {value_of_parameter}'
                escribirlog(msg)
        # save the file again
        with open(self.path,"wb") as file:
            pk.dump(o,file)

    @print_func_text
    def reinit_order(self):
        # if you're testing, this function is very usefull
        o={}
        with open(self.path,"wb") as file:
            pk.dump(o,file)
