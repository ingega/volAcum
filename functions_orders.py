from data import *
from functions_files import escribirlog,escribirerror, leerDic
from functions import BinanceAPIException
import time
from decorators import print_func_text
from tickers import Ticker

my_path = path

class Balance:
    def __init__(self,money):
        self.money = money
        self.pt = path / "avalaible_balance.txt"  # pt is for path

    def update_balance(self):
        # this function, substract balance from file
        with open(self.pt,"rb") as file:
            aval_bal=float(file.read())
            file.close()
        aval_bal -= self.money
        aval_bal = str(aval_bal)
        u_file = open(self.pt,"w")
        u_file.write(aval_bal)
        msg = f'the avalaible balance was set in {aval_bal}'
        escribirlog(msg)

    def set_balance(self):
        # this function, set the balance in the file
        u_file = open(self.pt, "w")
        u_file.write(str(self.money))
        msg=f'the avalaible balance was set in {self.money}'
        escribirlog(msg)



def checarAbiertas(ticker):
    from functions import cliente
    n=0
    abi=0
    while n < 5:
        try:
            ordenes = cliente.futures_get_open_orders(symbol=ticker)
            abi=len(ordenes)
            break
        except BinanceAPIException as error:
            n += 1
            a = n / 10
            msj="Binance generó un error consistente en " + "\n" + error.message + "\n" + "error No. " + str(error.code)
            escribirlog(msj)
            escribirerror(error.message, error.code)
            time.sleep(a)
    if n >= 5:
        msj="no fue posible sacar los datos de ordenes abiertas"
        escribirlog(msj)
        return "null"

    return abi

def checarOrden(simbolo,laorden):
    # ok sometimes if the order was just added  to the binance db
    # the system can't find it, so let's wait a pair of seconds
    # to execute search
    from functions import cliente
    time.sleep(2)
    n = 0
    salida=[]
    while n < 5:
        try:
            orden = cliente.futures_get_order(symbol=simbolo,orderId=laorden)
            cantidad = orden['origQty']
            cantidad=float(cantidad)
            posicion = orden['side']
            precio = orden['avgPrice']
            precioA = orden['price']
            epoch = orden['time']
            tiempo = int(epoch/1000)
            tiempo = time.asctime(time.gmtime(tiempo))
            fechaA = orden['updateTime']
            fechaA = int(fechaA/1000)
            fechaA = time.asctime(time.gmtime(fechaA))
            precio = float(precio)
            status = orden['status']
            parcial = float(orden['executedQty'])
            salida = {
                'cantidad':cantidad,
                'posicion':posicion,
                'precio':precio,
                'precioA':precioA,
                'epoch': epoch,
                'tiempo':tiempo,
                'status':status,
                'fechaA':fechaA,
                'parcial':parcial,
            }
            break
        except BinanceAPIException as error:
            #OJO si el error es -2013, es decir no la encuentra, entonces la buscamos en buscarOrdenes
            if error.code==-2013:
                msj="el sistema de binance genero error 2013, no encuentra la orden " + str(laorden)
                msj+=" se buscara de otra manera"
                escribirlog(msj)
                buscar=buscaOrdenes(simbolo,laorden)
                # para saber si encontró la orden, la imprimimos y le damos una pausa
                msj="el resultado de buscar es "
                msj+=str(buscar)
                escribirlog(msj)
                if len(buscar)>0:
                    if buscar['encontrado']==True:
                        salida = {
                            'cantidad': buscar['cantidad'],
                            'posicion': buscar['posicion'],
                            'precio': buscar['precio'],
                            'precioA': buscar['precioA'],
                            'tiempo': buscar['tiempo'],
                            'status': buscar['status'],
                            'fechaA': buscar['fechaA'],
                            'parcial': buscar['parcial'],
                        }
                        break
            n = n + 1
            a = n / 10
            msj = simbolo + error.message + "intento " + str(n) + " idOrden " + str(laorden)
            escribirerror(msj, error.code)
            print("Se ha generado un error al momento de sacar los datos de cantidad y side en checarOrden, el valor de orden es ", laorden,
                  ", en este momento son las ", time.ctime(), " hora gm\n"
                                                              " intento no. ", n)
            time.sleep(a)
        if n >= 5:
            msj="no se logro con 5 intentos revisar la orden " + str(laorden) + " la salida que se mandara es " + str(salida)
            escribirlog(msj)
            salida=0
    return salida

def buscaOrdenes(simbolo,idorden):
    #debido a que el checarOrden no aparecen algunas (como no llenas PE) si se comete el error -2013, la buscamos aqui
    n = 0
    b = 0
    salida = {}
    from functions import cliente
    while n < 5:
        try:
            ordenes=cliente.futures_get_open_orders()
            for a in ordenes:
                if a['symbol']==simbolo and a['orderId']==idorden:
                    msj="se ha encontrado la orden en buscarOrdenes, su estatus es " + a['status']
                    escribirlog(msj)
                    cantidad = a['origQty']
                    cantidad = float(cantidad)
                    parcial=a['executedQty']
                    parcial=float(parcial)
                    posicion = a['side']
                    precio = a['avgPrice']
                    precioA=a['price']
                    tiempo = a['time']
                    tiempo = int(tiempo / 1000)
                    tiempo = time.asctime(time.gmtime(tiempo))
                    fechaA=a['updateTime']
                    fechaA=int(fechaA/1000)
                    fechaA=time.asctime(time.gmtime(fechaA))
                    precio = float(precio)
                    status = a['status']
                    salida = {
                        'encontrado':True,
                        'cantidad': cantidad,
                        'posicion': posicion,
                        'precio': precio,
                        'precioA': precioA,
                        'tiempo': tiempo,
                        'status': status,
                        'fechaA': fechaA,
                        'parcial': parcial,
                    }
                    break
            if salida== {}:  #no encontro la orden, ahora la buscamos en sistema de todas las órdenes
                msj="no se encuentra la orden, nos vamos a sistema de todas las ordenes"
                escribirlog(msj)
                ordenes = cliente.futures_get_all_orders()
                for a in ordenes:
                    if a['symbol'] == simbolo and a['orderId'] == idorden:
                        msj = "se ha encontrado la orden en sistema de todas las órdenes, su estatus es " + a['status']
                        escribirlog(msj)
                        cantidad = a['origQty']
                        cantidad = float(cantidad)
                        parcial = a['executedQty']
                        parcial = float(parcial)
                        posicion = a['side']
                        precio = a['avgPrice']
                        precioA = a['price']
                        tiempo = a['time']
                        tiempo = int(tiempo / 1000)
                        tiempo = time.asctime(time.gmtime(tiempo))
                        fechaA = a['updateTime']
                        fechaA = int(fechaA / 1000)
                        fechaA = time.asctime(time.gmtime(fechaA))
                        precio = float(precio)
                        status = a['status']
                        salida = {
                            'encontrado': True,
                            'cantidad': cantidad,
                            'posicion': posicion,
                            'precio': precio,
                            'precioA': precioA,
                            'tiempo': tiempo,
                            'status': status,
                            'fechaA': fechaA,
                            'parcial': parcial,
                        }
                        break
            break
        except BinanceAPIException as error:
            msj="se cometio un error en el modulo buscarOrdenes "
            escribirlog(msj)
            n = n + 1
            b = n / 10
            escribirerror(error.message, error.code)
            time.sleep(b)
    if n >= 5:
        msj="despues de 5 intentos no se pudo obtener la info de buscarOrdenes "
        escribirlog(msj)
    return salida

def cancelarOrden(idorden, ticker):
    #cuando uno trata de cancelar una órden que ya se llenó, el sistema genera el error -2011, en este caso
    #simplemente informamos que ya estaba cancelada
    n=0
    a=0
    moneda = ticker
    salida=0
    from functions import cliente
    while n < 5:
        try:
            cliente.futures_cancel_order(symbol=moneda, orderId=idorden)
            salida=1
            return salida
        except BinanceAPIException as error:
            if error.code==-2011:
                print("Binance rechazó la cancelación de la orden ",idorden, " revise manualmente")
                salida=0
                break
            n = n + 1
            a = n / 10
            msj = str(idorden) + error.message + "intento " + str(n)
            escribirerror(msj, error.code)
            print("Se ha generado un error al momento de cancelar las ordenes "
                  ", en este momento son las ",
                  time.ctime(), " hora gm\n"
                                "intento no. ", n)
            time.sleep(a)
    if n >= 5:
        print("Se requiere el código de rescate")
        exit()
    return salida

@print_func_text
def obtenerCantidad(tk):  # ticker is a dictionary
    from functions import ultimoPrecio
    #OJO si autoentrada es True, entonces la entrada será diferente
    #los datos se debe de sacar del .txt para que se actualicen en tiempo real
    # qty in this strategy is with share balance
    ticker = Ticker(ticker=tk)
    Entrada = entrada
    data_ticker = ticker.read_ticker()[tk]
    precisionQty = data_ticker['qty_presicion']
    lvg = data_ticker['leverage']
    porcIn = data_ticker['porcIn']
    cantidad = 0
    cantidadMinima = data_ticker['min_qty']
    # get the maxIn
    if autoentrada == True:
        miArch = open("avalaible_balance.txt")
        dato = miArch.read()
        miArch.close()
        din = float(dato)
        In = din * porcIn
        # la mas nuevo de momentum, es que sólo puede perder hasta un limite,
        # para ganar no hay
        msj = f"money we'll use is {In} "
        escribirlog(msj)
        In = round(In,2)
    else:
        In = Entrada
    n = 0
    #debemos verificar que la entrada supere al mínimo notional
    # para evitar el rechazo de la compra
    #el dato lo tenemos en misdatos[entrada]
    if In < entrada:
        In = entrada
        In += 0.05   # add five cents to get the next rounded qty in case of
        msj = (f"actual entry is below of minimum requirement, "
               f"the entry was changed for {entrada} ")
        escribirlog(msj)
    # finalmente esta es la lana de entrada y se informa
    msj = f"the money used is {In} "
    escribirlog(msj)
    x = 0
    while n < 5:
        try:
            x = ultimoPrecio(tk)
            msj = f"the last price of ticker is {x} "
            escribirlog(msj)
            # ahora debemos verificar que la entrada si cumpla con el minimo
            cantidad = (In*lvg) / x
            # verificamos que si pasamos la cantidad minima pedida por binance
            if cantidad < cantidadMinima:
                cantidad = cantidadMinima
                msj=(f"the resulted money don't break the min "
                     f"necesary, rather {cantidad} ")
                escribirlog(msj)
            # mandamos la correcta precision para evitar errores
            cantidadO = cantidad  # ojo cantidad original
            # se usa para aquellos ticker que van enteros
            if precisionQty > 0:
                cantidad = round(cantidad, precisionQty)
            elif precisionQty == 0:
                # recordar que int toma el entero independiente del
                # decimal, 1.9999 será 1
                cantidadO = round(cantidadO)
                cantidad = int(cantidad)
                if cantidadO > cantidad:  # le falto uno
                    cantidad = int(cantidadO)
            # Ahora si, lista para tradear!!!!!!!
            break
        except BinanceAPIException as error:
            n = n + 1
            a = n / 10
            print("Se cometió un error en el modulo obtenerCantidad")
            escribirerror(error.message, error.code)
            time.sleep(a)
    if n >= 5:
        print("Se requiere el código de rescate")
        exit()
    msj = f"the qty obtained of {tk} was {cantidad} "
    escribirlog(msj)
    # the qty obtained, give us the maxLoss,
    # this qty must be susbstracted from avalaible_balance
    money_used = cantidad * x
    max_loss = money_used * slmax  # is the maximum amount of loss
    msg = f'the money used is {money_used} the max loss is {max_loss}'
    escribirlog(msg)
    # finally i need to subtract it from balance
    balance = Balance(max_loss)
    balance.update_balance()
    return cantidad

def mandarOrdenStop(simbolo,posicion,cantidad,precio):
    #OJo en las ordenes stop, se debe triggear en el precio y establcer uno abajo/arriba
    misdatos = leerDic(path / "ticker.txt")
    precision=misdatos['precision']
    presicion=1/(10**precision)
    if posicion=="BUY": # es un largo, se triggea en Sl, y la orden a poner en una posicion arriba
        precioIn=precio+presicion
    else: # Es un corto, se le pone uno abajo
        precioIn=precio-presicion
    precioIn=round(precioIn,precision)
    print("los datos a mandar, en la orden son:\n"
          " simbolo :", simbolo, "side :", posicion, "price :", precio, "stopPrice :", precioIn)
    n = 0
    a = 0
    salida=0
    from functions import cliente
    while n < 5:
        try:
            ordenSL = cliente.futures_create_order(
                symbol=simbolo,
                side=posicion,
                positionSide="BOTH",
                type="STOP",
                quantity=cantidad,
                price=precioIn,
                stopPrice=precio
                )
            salida = ordenSL['orderId']
            break
        except BinanceAPIException as error:
            if error.code==-2021: #OJO la orden se triggeo inmediatamente, mandamos de salida un -1
                salida=-1
            n = n + 1
            a = n / 10
            print("Se cometió un error en el modulo madarOrdenStop")
            escribirerror(error.message, error.code)
            time.sleep(a)
    if n >= 5:
        print("Se requiere el código de rescate")
        if salida>-1: #me salgo
            exit()
    return salida

def cancelarOrdenes(simbolo):
    n=0
    a=0
    from functions import cliente
    while n < 5:
        try:
            cliente.futures_cancel_all_open_orders(symbol=simbolo)
            break
        except BinanceAPIException as error:
            n = n + 1
            a = n / 10
            print("se cometio un error en el módulo de cancelarOrdenes")
            escribirerror(error.message, error.code)
            time.sleep(a)
    if n >= 5:
        print("Se requiere el código de rescate")
        exit()

def mandarOrdenTP(simbolo,cantidad, posicion, precio):
    n=0
    a=0
    salida=0
    from functions import cliente
    while n < 5:
        try:
            ordenTP = cliente.futures_create_order(
                symbol=simbolo,
                side=posicion,
                positionSide="BOTH",
                type="LIMIT",
                quantity=cantidad,
                price=precio,
                timeInForce="GTC")
            salida = ordenTP['orderId']
            break
        except BinanceAPIException as error:
            n = n + 1
            a = n / 10
            print("se cometio un error al momento de poner la ordenTp")
            escribirerror(error.message, error.code)
            time.sleep(a)
    if n >= 5:
        print("Se requiere el código de rescate")
        exit()
    return salida


@print_func_text
def mandarOrdenMercado(simbolo,posicion,cantidad, checar=False):
    n = 0
    a = 0
    from functions import cliente
    salida = 0
    # la nueva función es: si existe órden de ese ticker, no se ingresa
    adentro = checarOrdenAdentro(simbolo)
    if adentro['cantidad'] > 0: # a caracas, tenemos posición adentro
        msj = "en este momento hay una cantidad de " + str(adentro['cantidad'])
        msj += " por tanto no se hace la entrada"
        escribirlog(msj)
        salida=-1
    while n < 5:
        if salida==-1 and checar:
            break
        else:
            msj = ("los valores de salida y checar son "
                 + str(salida) + ","
                 + str(checar) + " por tanto si entra"
                 )
            escribirlog(msj)
        try:
            orden = cliente.futures_create_order(
            symbol=simbolo,
            side=posicion,
            positionSide="BOTH",  # Esto es por que estamos en el one-way mode
            type=cliente.ORDER_TYPE_MARKET,
            quantity=cantidad
            )
            salida = orden['orderId']
            break
        except BinanceAPIException as error:
            n = n + 1
            a = n / 10
            print("se cometio un error al momento de poner la orden mercado")
            escribirerror(error.message, error.code)
            time.sleep(a)
    if n >= 5:
        print("Se requiere el código de rescate")
        exit()
    return salida

def checarOrdenAdentro(ticker):
    from functions import cliente
    laOrden=cliente.futures_position_information(symbol=ticker)
    cantidad = 0
    price_in = 0
    if len(laOrden) > 0:
        laOrden=laOrden[0]
        price_in = float(laOrden['entryPrice'])
        cantidad = float(laOrden['positionAmt'])
    if cantidad!=0:
        if cantidad<0:
            posicion="SELL"
            posicionCierre="BUY"
        else:
            posicion = "BUY"
            posicionCierre = "SELL"
    else:
        posicion="NULL"
        posicionCierre="NULL"

    salida={
        'ticker':ticker,
        'cantidad':abs(cantidad),
        'precioIn':price_in,
        'posicion':posicion,
        'posicionCierre':posicionCierre,
    }
    return salida

def cerrarAMercado(ticker):
    # we can take out the data from the actives orders
    adentro=checarOrdenAdentro(ticker)
    if adentro['cantidad']==0:
        msj=f"there\'s no active order for {ticker} "
        escribirlog(msj)
        return
    # ahora la cerramos a mercado, tenemos posicion y cantidad
    if adentro['posicion']=="BUY":
        pos="SELL"
    else:
        pos="BUY"
    orden=mandarOrdenMercado(adentro['ticker'],pos,adentro['cantidad'])
    msj="se ha mandado cerrar a mercado en funcion."
    escribirlog(msj)
    # ahora saco la ganancia
    datosOrden=checarOrden(adentro['ticker'], orden)
    precioOut=datosOrden['precio']
    # el precioIn se tiene en adentro
    precioIn=adentro['precioIn']
    # adentro indica la posicion actual
    if adentro['posicion']=="BUY":
        ganancia=(precioOut-precioIn)/precioIn
    else:
        ganancia=(precioIn-precioOut)/precioIn
    ganancia -= 0.0008  # esto es por la ultima operacion
    # finalmente madamos la salida
    salida={
        'order_id': orden,
        'ganancia':ganancia,
        'orderId':orden,
        'priceOut':precioOut,
    }
    return  salida

def mandarOrdenStopMarket(simbolo,posicion,cantidad,precio):
    #OJo en las ordenes stop, se debe triggear en el precio y
    # establcer uno abajo/arriba
    tickers = Ticker(ticker=simbolo)
    ticker = tickers.read_ticker()
    precision = ticker[simbolo]['presicion']
    presicion = 1 / (10 ** precision)
    if posicion == "BUY": # es un largo, se triggea en Sl, y la
        # orden a poner en una posicion arriba
        precioIn = precio + presicion
    else:  # Es un corto, se le pone uno abajo
        precioIn = precio - presicion
    precioIn = round(precioIn, precision)
    print(f"los datos a mandar en la orden son: "
          f" ticker : {simbolo}, side :" 
          f"{posicion}, price : {precio}, stopPrice : {precioIn}")
    n = 0
    a = 0
    salida = 0
    from functions import cliente
    while n < 5:
        try:
            ordenSL = cliente.futures_create_order(
                symbol = simbolo,
                side = posicion,
                positionSide = "BOTH",
                type = "STOP_MARKET",
                quantity = cantidad,
                stopPrice = precio
                )
            salida = ordenSL['orderId']
            break
        except BinanceAPIException as error:
            if error.code==-2021:
                print("la orden se ejecutó inmediatamente, la salida será 0")
                salida=0
                break
            n = n + 1
            a = n / 10
            print("Se cometió un error en el modulo madarOrdenStop")
            escribirerror(error.message, error.code)
            time.sleep(a)
    if n >= 5:
        print("Se requiere el código de rescate")
        exit()
    return salida
