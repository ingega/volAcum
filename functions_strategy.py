import data
from functions_files import escribirlog, leerDic, escribirerror, escribirDic
from functions_orders import (checarOrden, cancelarOrden,
                              obtenerCantidad, mandarOrdenStopMarket)
from functions_orders import checarOrdenAdentro, cancelarOrdenes
from functions_orders import mandarOrdenTP, mandarOrdenMercado, cerrarAMercado
from functions import cliente, miMail, BinanceAPIException
import time
from functions import datosSalida
from tickers import Ticker
from orders import Order
from decorators import print_func_text
from main import get_all_pairs_opor
from strategy import make_3bp_entries



def checkInit():
    # this function check if any order it's open
    msg = "we're init da checkInit module "
    escribirlog(msg)
    Data = leerDic(data.path / "order.txt")
    ticker = Data['ticker']
    buyOrder = Data['buyOrder']
    sellOrder = Data['sellOrder']
    p = 0
    while True:
        checkBuy = checarOrden(ticker, buyOrder)
        checkSell = checarOrden(ticker, sellOrder)
        statusBuy=checkBuy['status']
        statusSell=checkSell['status']
        if statusSell=='FILLED':  # SELL order won
            Data['side'] = 'SELL'
            Data['orderA']=sellOrder
            Data['priceIn']=checkSell['precio']
            Data['originalPrice']=checkSell['precio']
            Data['dateIn']=time.time()
            escribirDic(data.path / "order.txt",Data)
            # we must cancell the other order, in this case, buyOrder
            cancel=cancelarOrden(buyOrder, ticker)
            msj="the sell order won, now we proceed to stablish tp/sl orders, and buy order it's canceled with idOrden " + str(cancel)
            escribirlog(msj)
            # stablish orders
            establecerOrdenes(0)
            # let's go to protect()
            while True:
                checkP=protect()
                if checkP==0:
                    break
                else:
                    msg="the system hit sl, we call protect() by hismself "
                    escribirlog(msg)
            break
        elif statusBuy=='FILLED':
            Data['side']='BUY'
            Data['orderA'] = buyOrder
            Data['priceIn'] = checkBuy['precio']
            Data['originalPrice'] = checkBuy['precio']
            Data['dateIn']=time.time()
            escribirDic(data.path / "order.txt", Data)
            # we must cancell the other order, in this case, sellOrder
            cancel = cancelarOrden(sellOrder, ticker)
            msj = "the buy order won, now we proceed to stablish tp/sl orders, and sell order it's canceled with idOrder " + str(
                cancel)
            escribirlog(msj)
            miMail(msj)
            # stablish orders
            establecerOrdenes(0)
            # let's go to protect()
            while True:
                checkP = protect()
                if checkP == 0:
                    break
                else:
                    msg = "the system hit sl, we call protect() by hismself "
                    escribirlog(msg)
            break
        else:
            time.sleep(data.timeframe)
            p+=1
            if p>300:
                msj="system work on original open, everething it's fine"
                escribirlog(msj)
                p=0
            hour = time.gmtime().tm_hour
            minute = time.gmtime().tm_min
            second = time.gmtime().tm_sec
            hour %= 4
            if hour == 0 and minute == 59 and second > 50:
                msj="system work on original open, everething it's fine"
                escribirlog(msj)
                miMail(msj)
                time.sleep(10)


def bothSidesOrders(ticker,price):
    msj="we're init da bothSideOrders module, the price that we'll use is " + str(price)
    escribirlog(msj)
    qty=obtenerCantidad()
    Data=leerDic(data.path / "ticker.txt")
    precision=Data['precision']
    # upPrice = price*(1+distance)
    # upPrice=round(upPrice,precision)
    upPrice = 0
    buyOrder=mandarOrdenStopMarket(ticker,"BUY",qty,upPrice)
    msj="we set the buy order with orderId " + str(buyOrder)
    escribirlog(msj)
    # sell order
    # downPrice = price * (1 - distance)
    # downPrice = round(downPrice, precision)
    downPrice = 0
    sellOrder = mandarOrdenStopMarket(ticker, "SELL", qty, downPrice)
    msj = "we set the sell order with orderId " + str(sellOrder)
    escribirlog(msj)
    # let's update the order.txt
    Data=leerDic(data.path / "order.txt")
    Data['buyOrder']=buyOrder
    Data['sellOrder']=sellOrder
    Data['qty']=qty
    escribirDic(data.path / "order.txt",Data)
    # now let's check it
    checkInit()   # to the end of in
    msj = "we're finish da bothSideOrders module"
    escribirlog(msj)


@print_func_text
def getEntry(ticker,side):
    # first step, get quantity
    qty = obtenerCantidad(ticker)
    order = mandarOrdenMercado(ticker,side,qty,False)
    time.sleep(5)
    msg = f"The market order in {side} of {ticker} was successfully "
    escribirlog(msg)
    ret = {
        'orderId':order,
        'qty':qty,
    }
    return ret


def error_close(side, ticker):
    cierre = cerrarAMercado(ticker)
    ganancia = cierre['ganancia']
    # we must update the dateOut and priceOut
    actualOrder = leerDic(data.path / "order.txt")
    actualOrder['dateOut'] = time.time()
    actualOrder['priceOut'] = cierre['priceOut']
    actualOrder['side']=side
    escribirDic(data.path / "order.txt", actualOrder)
    datosSalida(ticker, ganancia, "error")


@print_func_text
def establecerOrdenes(orden, ticker):  # order = 0 is for initial bet
    # tomaremos los datos de la orden adentro actual y debemos establecer
    # los valores, si la orden es cero, es la apuesta inicial
    # requerimos los datos de la apuesta, sl y tp
    # we can open the ticker and read the parameters
    tk = Ticker(ticker=ticker)
    mis_datos = tk.read_ticker()[ticker]
    precision_cantidad = mis_datos['qty_presicion']
    precision = mis_datos['presicion']
    order = Order(ticker=ticker)
    datos_orden = order.read_order()[ticker]
    ajuste_loss = datos_orden['adjust']
    orden_actual = checarOrdenAdentro(ticker)
    cantidad = orden_actual['cantidad']
    lacantidad = cantidad * 2
    lacantidad = round(lacantidad, precision_cantidad)  # solo por que python de
    # repente agrega decimales a los float
    # OJO es importante saber que puede haber cantidades
    # "residuales" fastidiando, se deben eliminar manualmente
    posicion = orden_actual['posicionCierre']
    precioIn = orden_actual['precioIn']
    if orden_actual['posicion'] == "BUY":
        # los precios son depende la orden (0 es apuesta inicial)
        if orden == 0:
            precioSL = precioIn * (1 - data.bet)
            precioTP = precioIn * (1 + data.bet)
        else:
            precioSL=precioIn*(1 - data.sl)
            precioTP=precioIn*(1 + data.tp + ajuste_loss)
    else:
        if orden == 0:
            precioSL = precioIn * (1 + data.bet)
            precioTP = precioIn * (1 - data.bet)
        else:
            precioSL = precioIn * (1 + data.sl)
            precioTP = precioIn * (1 - data.tp - ajuste_loss)
    precioTP = round(precioTP,precision)
    precioSL = round(precioSL,precision)
    ordensl = mandarOrdenStopMarket(ticker, posicion, lacantidad, precioSL)
    msj = (f"the SL and pullback order was seted in price "
         f"{precioSL}  with orderId {ordensl} ")
    escribirlog(msj)
    '''
    OK, but what if couldn't set the order? 
    the may 14th of 2024 i have this issue, and i get 0 in ordersl
    let's do this: the only reasson that could be possible is that 
    price now is out of trigger price, i mean, have quickly
    pull down, push up, so in order to fixed it, if 
    ordensl = 0, that's mean that the actual price is over the sl
    so, can we make two things: 
    1. if the price is "near" of the next sl, 
    we can close everything, and get and market
    order, make calculation of loss and go on, 
    2. or simply close and get out
    for the moment i take the second one
    '''
    if ordensl == 0:  # let's go
        msg=("The orderSL is 0, the pullback/pushup must be agressive, "
             "so in order to prevent more losses, the bot call error_close")
        escribirlog(msg)
        miMail(msg)
        e = error_close(posicion,ticker)
        # well, let's remove the ticker from orders and tickers
        ticker.del_ticker()
        order.del_order()
        return
    # now the tp order
    ordentp = mandarOrdenTP(ticker,cantidad,posicion,precioTP)
    msj = f"the TP order has seted in price {precioTP} with orderId {ordentp} "
    escribirlog(msj)
    # let's update the order
    order.update_order(orderSL=ordensl, orderTP=ordentp)
    # if necessary, cancel the open orders remain
    if orden > 1:
        c = cancelarOrden(orden,ticker)
        if c != 0:
            msj=f"cancel order, was succesfully, the idOrder was {orden} "
            escribirlog(msj)


@print_func_text
def buscaManual(ticker):
    # this module review the open orders, in order to find the status of ticker
    parcial = []
    abiertas = cliente.futures_get_open_orders(symbol=ticker)
    if len(abiertas) > 0:
        for a in abiertas:
            parcial.append(a)
    salida = {
        'abiertas': len(abiertas),
        'ordenes': parcial,
    }
    return salida


def tie_exit(ticker):
    cierre = cerrarAMercado(ticker)
    ganancia = cierre['ganancia']
    msg=f'the partial profit for this operation in {ticker} is {ganancia}'
    escribirlog(msg)
    # we must update the dateOut and priceOut
    order=Order(ticker=ticker)
    # the operation must be added to the db, and adjust change the type
    order_data = order.read_order()
    the_type = "indirect_sl" if (
            order_data[ticker]['adjust'] >= data.slmax) else "end"
    data_cierre = checarOrden(ticker, cierre['order_id'])
    from strategy import get_trade, get_fee
    trade = get_trade(ticker,
                      order_data[ticker]['orderSL']
                      )
    commission = trade['commission']
    pnl = trade['pnl']
    # and obviusly we need the operation_id
    operation_id = order_data[ticker]['operation_id']
    # fee
    fee = get_fee(ticker=ticker, operation_id=operation_id)
    new_record = {
        'strategy': [data.sistema],
        'ticker': [ticker],
        'side': [order_data[ticker]['side']],
        'quantity': [data_cierre['cantidad']],
        'price': [data_cierre['precio']],
        'type': [the_type],
        'commission': [commission],
        'fee': [fee['fee']],
        'epoch_fee': [fee['epoch_fee']],
        'operation_id': [operation_id],
        # is sl update
        'binance_operation_id': [order_data[ticker]['orderSL']],
        'epoch': [data_cierre['epoch']],
        'pnl': [pnl]
    }
    from db import Record
    record = Record()
    record.add_record(record=new_record)
    order.update_order(dateOut=time.time(),priceOut=cierre['priceOut'])
    # and finally cancel openOrders
    cancelarOrdenes(ticker)
    # and return the profit
    return ganancia


@print_func_text
def make_exit(ticker, adjust, outcome):
    # ok once the order is execute, we have a price, so, let's update
    order = Order(ticker=ticker)
    data_order = order.read_order()[ticker]
    # in every case we need the side, priceIn and priceOut,
    # and profit of course
    price_in = data_order['priceIn']
    price_out = data_order['priceOut']
    side = data_order['side']
    if side == "BUY":
        profit = (price_out-price_in) / price_in
    else:
        profit = (price_in - price_out) / price_in
    # remove the last comission too
    profit -= adjust + 0.0008
    # we must check if is direct or indirect bet
    if outcome=='TP':
        if adjust == 0:
            outcome = "direct TP"
        elif adjust > 0:
            outcome = "Indirect TP"
        else:
            profit = 0
            outcome = f"Incongruent value {adjust}"
    elif outcome == 'SL':
        profit = -adjust  # in sl the adjust is already calculated
        msg = (f'{ticker} fall in sl, the side was '
               f'{side} and the adjust was {profit}, '
               f'the total adjust is {adjust} '
               f'but this is in make_exit ')
        escribirlog(msg)
        miMail(msg)
        outcome = "sl"
    else: # there's only tie left
        profit = adjust  # in tie we use this parameter for profit
    msj = (f"the outcome is {outcome}, data are priceIn {price_in}, "
           f"priceOut: {price_out} side {side}, profit {profit} call exit ")
    escribirlog(msj)
    # before get the exit data, is necesarie update the dateOut
    if outcome!='tie':  # otherwise is not necesary
        order.update_order(dateOut=time.time())
    datosSalida(ticker, profit, outcome)


def order_not_found(ticker,orderId):
    abiertas = buscaManual(ticker)
    status=""
    if abiertas['abiertas'] == 0:
        msj = f"order {orderId} doesn\'t founded for binance API, neither with manual search "
        escribirlog(msj)
        miMail(msj)
        raise Exception(f"is not posible review the order {orderId} by protect function")
    elif abiertas['abiertas'] == 1:  # revisamos su tipo de orden
        tipo = abiertas['ordenes'][0]['type']
        msj = f"there\'s only open order and its type is {tipo} "
        escribirlog(msj)
        if tipo == "LIMIT":  # la orden limit esta viva pero sola, por tanto la stop_market se llenó
            status = abiertas['ordenes'][0]['status']
        elif tipo == "STOP_MARKET":
            status = "FILLED"  # debido a que la stop sigue abierta, pero no podemos sacar el precio
    elif abiertas['abiertas'] == 2:  # no pasa nada, sigue NEW, no es neceario actualizar el precio
        status = "NEW"
    else:  # demasiadas ordenes abiertas
        msj = f"there\'s {len(abiertas)} orders for this ticker, please review the code and other\'s strategies ticker conflict "
        escribirlog(msj)
        miMail(msj)
        raise Exception("Too many open orders")
    return status


@print_func_text
def protect():
    # this funciton review constantly (every data.timeframe seconds)
    # if any order has executed, the posibles matchtes are:
    # directTP, indirectTP, sl and tie only,
    # protect review all the tickers added in orders.pkl
    while True:
        order = Order()
        actual_orders = order.read_order()
        if len(actual_orders)>0: # we have tickers to review
            while True:  # break gets when len(order)==0
                time.sleep(data.timeframe)
                # in some points, every orders may be executed
                order = Order()
                actual_orders = order.read_order()
                if len(actual_orders)==0:
                    break
                for ticker in actual_orders:
                    # simply as review booth orders,
                    # starts always with sl, because need protection
                    sl_order = checarOrden(ticker,
                                           actual_orders[ticker]['orderSL'])
                    if sl_order == 0:
                        status_sl = order_not_found(
                            ticker,
                            actual_orders[ticker]['orderSL']
                        )
                    else:
                        status_sl = sl_order['status']
                    if status_sl == 'FILLED':
                        """
                        well, in this case, 
                        we need adjust the loss and call 
                        establecerOrdenes with orderTP
                        if we want precision, we need the side, 
                        and the priceOut, this way we have more 
                        accurate the outcomes
                        """
                        # after any move, let's send into db
                        from strategy import get_trade, get_fee
                        trade = get_trade(ticker,
                                           actual_orders[ticker]['orderSL']
                                          )
                        commission = trade['commission']
                        pnl = trade['pnl']
                        # and obviusly we need the operation_id
                        operation_id = actual_orders[ticker]['operation_id']
                        # fee
                        fee = get_fee(ticker=ticker, operation_id=operation_id)
                        new_record = {
                            'strategy': [data.sistema],
                            'ticker': [ticker],
                            'side': actual_orders[ticker]['side'],
                            'quantity': sl_order['cantidad'],
                            'price': [sl_order['precio']],
                            'type': ['sl'],
                            'commission': [commission],
                            'fee': [fee['fee']],
                            'epoch_fee': [fee['epoch_fee']],
                            'operation_id': [operation_id],
                            # is sl update
                            'binance_operation_id': [actual_orders[ticker]['orderSL']],
                            'epoch': [sl_order['epoch']],
                            'pnl': [pnl]
                        }
                        # let's added into a db
                        from db import Record
                        record = Record()
                        record.add_record(record=new_record)
                        # this is the preview price
                        priceIn = actual_orders[ticker]['priceIn']
                        # this is the price executed in stop_market
                        priceOut = sl_order['precio']
                        # this is the side for loss
                        side = actual_orders[ticker]['side']
                        # preview adjust
                        adjust = actual_orders[ticker]['adjust']
                        # let's get the loss profit
                        # is absolute, don't matter the side
                        profit = abs((priceOut-priceIn)/priceIn)
                        # we need that order is pointing to a ticker
                        order_sl = Order(ticker=ticker)
                        # well, if bet_continue we always must re-set the epoch
                        if data.bet_continue:
                            order_sl.update_order(epochIn=time.time())
                        else:
                            # if is the first sl, we need to update the epochIn
                            if adjust == 0: # the original bet change
                                # the adjust value
                                order_sl.update_order(epochIn=time.time())
                        adjust += profit + 0.0008
                        # ok now we gonna flip the position,
                        # and also the priceOut now is the priceIn
                        if side == 'BUY':
                            side = "SELL"
                        else:
                            side = "BUY"
                        # update in orders
                        order_sl.update_order(adjust=adjust,
                                              side=side, priceIn=priceOut)
                        if adjust >= data.slmax: # see you later aligator
                            # we need to close the last operation
                            profit = tie_exit(ticker)
                            # update adjust
                            adjust += profit
                            # for debug matters
                            msg = (f'{ticker} go to sl, '
                                   f'the side was {side} '
                                   f'and the adjust was '
                                   f'{profit}, '
                                   f'the total adjust is '
                                   f'{adjust} ')
                            escribirlog(msg)
                            miMail(msg)
                            make_exit(ticker, adjust,'SL')
                            break
                        # before of orderStablish, send the mail
                        msg = f'{ticker} fall in sl, the side was {side} and the adjust was {profit}, the total adjust is {adjust} '
                        escribirlog(msg)
                        miMail(msg)
                        # let's call establecerOrdenes
                        establecerOrdenes(actual_orders[ticker]['orderTP'],ticker)
                    # now the tp
                    tp_order=checarOrden(ticker, actual_orders[ticker]['orderTP'])
                    if tp_order==0:
                        status_tp=order_not_found(ticker,actual_orders[ticker]['orderTP'])
                    else:
                        status_tp=tp_order['status']
                    if status_tp=='FILLED':  # winner winner chicken dinner
                        # add the record
                        from strategy import get_trade, get_fee
                        # commission and pnl
                        trade = get_trade(ticker,
                                          actual_orders[ticker]['orderTP']
                                          )
                        commission = trade['commission']
                        pnl = trade['pnl']
                        # and obviusly we need the operation_id
                        operation_id = actual_orders[ticker]['operation_id']
                        # fee
                        fee = get_fee(ticker=ticker, operation_id=operation_id)
                        # the type changes in tp
                        the_type = "indirect_tp" \
                            if actual_orders[ticker]['adjust'] \
                            else "direct_tp"
                        new_record = {
                            'strategy': [data.sistema],
                            'ticker': [ticker],
                            'side': actual_orders[ticker]['side'],
                            'quantity': tp_order['cantidad'],
                            'price': [tp_order['precio']],
                            'type': [the_type],
                            'commission': [commission],
                            'fee': [fee['fee']],
                            'epoch_fee': [fee['epoch_fee']],
                            'operation_id': [operation_id],
                            # is sl update
                            'binance_operation_id': [actual_orders[ticker]['orderSL']],
                            'epoch': [sl_order['epoch']],
                            'pnl': [pnl]
                        }
                        # let's added into a db
                        from db import Record
                        record = Record()
                        record.add_record(record=new_record)
                        # we need to update the priceOut, in limit orders are the 'precio' field
                        price_out=tp_order['precio']
                        date_out=time.time()  # the exactly is in tp_order data
                        # is time to add the record
                        # update order
                        order=Order(ticker=ticker)
                        order.update_order(priceOut=price_out, dateOut=date_out)
                        make_exit(ticker, actual_orders[ticker]['adjust'], 'TP')
                        # cancel the sl order and exit
                        cancelarOrdenes(ticker)
                        break
                        # in Exit, the order and ticker will be removed,
                        # so any action is necessary
                    # now wee need to review the time ellapsed for tie
                    r=order.read_order()[ticker]
                    if r['epochIn']>0:
                        time_elapsed=time.time()-r['epochIn']
                        if time_elapsed>(60 * data.barras):  # bars is in minutes
                            # inform, then make exit with getEntry,
                            # then call dataExit
                            msg=(f'the time elapsed for tie is '
                                 f'{time_elapsed} secs, '
                                 f'is time for declare a tie ')
                            escribirlog(msg)
                            profit=tie_exit(ticker)
                            # in tie, we need subtract the adjust
                            adjust=r['adjust']
                            profit -= adjust
                            make_exit(ticker,profit,"tie")
                # after review all orders, we need to inform about the function status, but also review if any ticker
                # get the 3bp
                review()
        else:
            break


def review():
    actual_hour = time.gmtime().tm_hour  # las horas
    actual_minutes = time.gmtime().tm_min  # los minutos
    actual_seconds = time.gmtime().tm_sec
    actual_hour %= data.hours
    actual_minutes %= data.minutes
    # we must notify to email
    # we need review of any ticker get the 3bp
    if (
            actual_hour == data.hours - 1
            and actual_minutes == data.minutes - 1
            and actual_seconds > data.seconds
    ):
        msg=f'is time to check for new oportunities, gmtime is {time.gmtime()}'
        escribirlog(msg)
        g=get_all_pairs_opor()
        msg=f'the value for g is {g}'
        escribirlog(msg)
        df_in = g['df_in']
        if len(df_in)>0: # well, in this case, the tickers inside
            # must be removed from the list, so
            # the better way to do this is using
            # map objects and the substract
            tickers_opor=map(str,df_in['ticker'])
            order=Order()
            tickers_in=order.read_order()
            # then get the elements that not are inside right now
            result = [item for item in tickers_opor if item not in tickers_in]
            if len(result)>0:
                df_in = df_in[df_in['ticker'].isin(result)]
                # send mail to inform
                msg=(f"in review locate an oportunitie in {len(df_in)} "
                     f"tickers {df_in}")
                escribirlog(msg)
                miMail(msg)
                make_3bp_entries(df_in)
                # and that's it, because the system remanins in protect()
        else:
            msg=f"system works normally, the gmtime is {time.gmtime()} sended by review "
            escribirlog(msg)
            miMail(msg)
        time.sleep(16)  # cicling avoid


def checarOrdenesAbiertas(ticker):
    n=0
    salida=0
    while n<5:
        try:
            abiertas=cliente.futures_get_open_orders(symbol=ticker)
            salida = {
                'numero':len(abiertas),
                'ordenes':abiertas,
            }
            break

        except BinanceAPIException as error:
            n = n + 1
            a = n / 10
            msj="Se cometió un error en el modulo checarAbiertas, intento no. " + str(n)
            escribirlog(msj)
            escribirerror(error.message, error.code)
            time.sleep(a)
    return salida


def check_init_tickers(ticker):
    order = Order()
    data_order = order.read_order()
    data_order=data_order[ticker]
    Adentro = checarOrdenAdentro(ticker)
    Abiertas = checarOrdenesAbiertas(ticker)
    laQty = Adentro['cantidad']
    if laQty != 0:  # atención hay orden adentro, checamos las abiertas
        ordenesA = Abiertas['numero']
        # si tiene cero, es error, se mandaría cerrar a mercado
        # si tiene 1, es otro error, pero este viene o, del inicial o del SL, o del TP, esto se puede reparar viendo ordenes.txt
        # si tiene 2, debería ser normal
        # si tiene mas de 2, na, es error no reparable, se mandaría cerrar a mercado
        if ordenesA == 0:
            # in this case, the system are in the init of orderStablish (the open orders in this point was canceled) so
            # the only way to reach this point is in the original bet, so, let's stablish orders with 0 (original bet)
            # so, the system never reach the order stablish, so must send to orderStablish with 0
            msj = "system come from error, there's one in and no opens, so let's stablish original bet "
            escribirlog(msj)
            miMail(msj)
            establecerOrdenes(0, ticker)
            protect()
        elif ordenesA == 1:  # solo puede venir de la inicial o de SL/TP, esto se ve en order.txt
            # lo que no podríamos hacer es ver el número de orden, ya que la posicion no lo indica, dejaríamos el mismo
            orden_actual = data_order['orderA']
            if orden_actual > 0:  # ojo, viene de sl/tp
                # ya tengo la cantidad en lacantidad, y la posicion en laPos, saco los datos de presicion, etc
                orderIdAbierta = Abiertas['ordenes'][0]['orderId']
                msj = f"it was an open, and an acive orders, next step is set sl and tp orders "
                escribirlog(msj)
                miMail(msj)
                establecerOrdenes(orderIdAbierta,ticker)
                protect()
        elif ordenesA > 2:
            msj = f"there´s a critical error, we have an actual inside order, and {ordenesA} open orders"
            escribirlog(msj)
            miMail(msj)
        else:  # todo en orden, una adentro, dos abiertas, ahora debemos ver si nos vamos a iniciales o a revisar
            # vamos a revisar algunas cosas, por ejemplo, si es dia de cambio, y gana uno de mi misma linea, y tiene
            # orden en ese momento, va a cometer error, así, vamos a checar si existe en order.txt
            try:
                print(f"orderTP is {data_order['orderTP']} ")
            except:
                msj = f"maybe the system comes from a change, and also in debug mode, because orderTP raise an error"
                escribirlog(msj)
                return True
            msj = f"system goes on error, but everything is fine, we've 2 opens and 1 inside orders "
            msj += f"the orderTP is {data_order['orderTP']} let's go to protect()"
            escribirlog(msj)
            miMail(msj)
            protect()
    else:  # there's no acative orde, but maybe is a double bet system, depends on open orders
        if Abiertas['numero'] == 0: # no active, no opens, remove it from orders
            msj = "system doesn't have open or in orders, this is an initial system "
            escribirlog(msj)
            order=Order(ticker=ticker)
            order.del_order()
            # also in ticker
            tk = Ticker(ticker=ticker)
            if ticker in tk.read_ticker():  # maybe is in order, but not in ticker
                tk.del_ticker()
        elif Abiertas['numero'] == 2:
            # son las iniciales a la espera de abrirse, se manda a checarApertura
            checkInit()
        elif Abiertas['numero'] == 1:  # if bot stop and stop order or tp order has been executed the outcome function don't update data
            # so, let's see which of one of the orders are open
            # ok if the order type=='LIMIT' the stop order won, and else the limit won
            from functions import ultimoPrecio
            currentOrder = Abiertas['ordenes'][0]
            side = currentOrder['side']
            exec_price = float(currentOrder['stopPrice'])
            actual_price = ultimoPrecio(ticker)
            adjust = data_order['adjust']
            if currentOrder['type'] == 'LIMIT':  # the SL order won, now, we can send to stablish order, but only if current price
                # it's below/above the entrance price (it means, that we have a profit, otherwise for safety stop the order
                # first we need the side
                if side == "BUY":  # loss below
                    slPrice = exec_price * (1 - data.sl)  # need this to check if price is out of bet bounds
                    if actual_price > slPrice:  # we're in price bounds, but need to check adjust
                        # adjust, side, priceIn
                        adjust += data.sl
                        order.update_order(adjust=adjust,side=side,priceIn=exec_price)
                        establecerOrdenes(currentOrder['orderId'], ticker)
                        protect()
                        return None
                    else:  # no more gone, let's call the finish function
                        # just need to update order data and make datosSalida(), dateOut, priceOut
                        dateOut = currentOrder['updateTime'] / 1000
                        priceOut = currentOrder['price']
                        order.update_order(dateOut=dateOut,priceOut=priceOut)
                        priceIn = data_order['priceIn']
                        adjust = data_order['adjust']
                        profit = ((priceOut - priceIn) / priceIn) - adjust - data.sl - 0.0008  # the last commission and sl
                        datosSalida(ticker,profit,"tie")  # maybe is not a tie
                        return None
                elif side == "SELL":  # loss above
                    slPrice = exec_price * (1 + data.sl)  # need this to check if price is out of bet bounds
                    if actual_price < slPrice:  # we're in price bounds
                        # adjust, side, priceIn
                        adjust += data.sl
                        order.update_order(adjust=adjust,side=side,priceIn=exec_price)
                        establecerOrdenes(currentOrder['orderId'],ticker)
                        protect()
                        return None
                    else:  # no more gone, let's call the finish function
                        # just need to update order data and make datosSalida(), dateOut, priceOut
                        dateOut = currentOrder['updateTime'] / 1000
                        priceOut = currentOrder['price']
                        order.update_order(dateOut=dateOut,priceOut=priceOut)
                        priceIn = data_order['priceIn']
                        adjust = data_order['adjust']
                        profit = ((priceIn - priceOut) / priceIn) - adjust - 0.0008  # the last commission
                        datosSalida(ticker,profit, "tie")  # maybe is not a tie
                        return None
            else:  # the tp order won, if adjust>0 is indirectTP else directTP
                if adjust > 0:  # indirectTP
                    outcome = "indirect TP"
                    profit = data.tp - 0.0008
                else:
                    outcome = "direct TP"
                    profit = data.bet - 0.0008
                order.update_order(dateOut=currentOrder['updateTime'],priceOut=currentOrder['price'])
                datosSalida(ticker,profit, outcome)
                return None
        else:  # cosa incongruente, cancelamos y le damos pa adelante
            from functions_orders import cancelarOrdenes
            msj = "el sistema tiene " + str(Abiertas['numero']) + " abiertas y nada adentro, simplemente cancelamos "
            escribirlog(msj)
            cancelarOrdenes(ticker)


@print_func_text
def init():
    # the first thing we need to do, is check the len or orders
    order = Order()
    data_order = order.read_order()
    if len(data_order)>0: # there's active tickers, let's iterate
        for ticker in data_order:
            check_init_tickers(ticker)
    else:
        # check if tickers have data
        ticker = Ticker()
        data_ticker = ticker.read_ticker()
        if len(data_ticker) > 0:  # there's active tickers, let's iterate
            msg = (f"there's {len(data_ticker)} in "
                   f"tickers.pkl, let's clean it")
            escribirlog(msg)
            for ticker in data_ticker:
                partial_ticker = Ticker(ticker=ticker)
                partial_ticker.del_ticker()
        msg=f"this is an initial system, there's no one active ticker in this moment"
        escribirlog(msg)
        miMail(msg)


def main():
    pass


if __name__ == '__init__':
    main()