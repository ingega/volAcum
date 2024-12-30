from binance.exceptions import BinanceAPIException
import data
from sendmail import enviarcorreo
from functions_files import *
from main import *
from decorator import print_func_text


cliente = Client(key.api_key, key.api_secret,requests_params={'timeout': 30})

path=data.path

def miMail(msj,filepath=None):
    ticker=leerDic(path+"ticker.txt")['ticker']
    asunto=data.sistema+ " " + data.usuario+" bahia" + str(data.bahia) + ":" + ticker
    enviarcorreo(asunto,msj,filepath)

def rescate():
    salida=False
    print("proceso de rescate terminado")
    return salida

#se requieren contadores de tiempo, leer barras poner ordenes limit/stop, checar ordenes, cancelarlas

def cambiarleverage(simbolo,lvg):
    msg="we're in begin of cambiarLeverage"
    escribirlog(msg)
    n = 0
    lvgA=lvg
    while n < 5:
        try:
            cliente.futures_change_leverage(symbol=simbolo,leverage=lvgA)
            # informo desde aqui
            msj="se ha cambiado el lvg por " + str(lvgA)
            escribirlog(msj)
            break
        except BinanceAPIException as error:
            #el error -4028 es simplemente lvg no valido, restamos 1 al lvg hasta llegar a uno válido
            if error.code==-4028:
                lvgA-=1
                msj=f'leverage {lvg} is not suported, next try is with {lvgA}'
                escribirlog(msj)
                #si el lvg es cero, pasamos n a 6
                if lvgA<=0:
                    msg=f'system can\'t set the leverage for {simbolo} the return function will be 0, but atention is required'
                    escribirlog(msg)
                    miMail(msg)
                    return 0
            else:
                n = n + 1
                a = n / 10
                msj = error.message + "intento " + str(n)
                escribirerror(msj, error.code)
                print("Se ha generado un error al momento de ajustar el leverage, "
                      " en este momento son las ",
                      time.ctime(), " hora gm\n"
                    "intento no. ", n)
                time.sleep(a)
    return lvgA

# ahora la media:

def listaPandas(lista):
    columnas = ["fecha", "open", "high", "low", "close", "epoch", "epochFin", "volumen"]
    nuevo = pd.DataFrame(lista,index=None,columns=columnas)
    return nuevo

def ultimoPrecio(moneda):
    intervalo="1m"
    n = 0
    a = 0
    precio=0
    while n < 5:
        try:
            precio = cliente.futures_klines(symbol=moneda, interval=intervalo, limit=1)[0][4] #el 4 es el close
            precio=float(precio)
            break
        except BinanceAPIException as error:
            n = n + 1
            a = n / 10
            escribirerror(error.message, error.code)
            time.sleep(a)
    if n >= 5:
        print("Se requiere el código de rescate")
        b = rescate()
        if b == False:
            exit()
    return precio

def borrarArchivos():
    miArch=open(path+"order.txt","w")
    miArch.write("")
    miArch.close()
    #además se cancelan las ordenes abietas
    misDatos=leerDic(path+"ticker.txt")
    ticker=misDatos['ticker']
    from functions_orders import cancelarOrdenes
    cancelarOrdenes(ticker)

def obtenerSaldo():
    dicto=leerDic(path+"ticker.txt")
    asset=dicto['quoteAsset']   #para que me de el saldo en el asset correcto
    n=0
    a=0
    saldo=0
    while n<5:
        try:
            checarsaldo = cliente.futures_account_balance()
            for a in checarsaldo:
                if a['asset'] == asset:
                    saldo = a['balance']
                    saldo = float(saldo)
                    saldo = round(saldo, 2)
            break
        except BinanceAPIException as error:
            n = n + 1
            a = n / 10
            print("Se cometio un error en el modulo obtenerSaldo")
            escribirerror(error.message, error.code)
            time.sleep(a)
    if n>=5:
        msj="no se pudo obtener el saldo"
        escribirlog(msj)
        miMail(msj)

    return saldo

def cambiarSaldo(saldoN): # nuevo saldo
    #checamos primero el saldo "viejo"
    saldoA=Archivo(data.pathGan+"balance.txt")
    miArch=open(data.pathGan+"balance.txt","w")
    miArch.write(str(saldoN))
    miArch.close()
    msj="The old balance was: " + saldoA + " the new one: " + str(saldoN)
    escribirlog(msj)

@print_func_text
def updateLocalBalance(NBalance): # nuevo saldo
    #checamos primero el saldo "viejo"
    saldoA=Archivo(path+"balance.txt")
    miArch=open(path+"balance.txt","w")
    miArch.write(str(NBalance))
    miArch.close()
    msj="The old local balance was: " + saldoA + " the new one: " + str(NBalance)
    escribirlog(msj)

def update_avalaible_balance(money):
    from functions_orders import Balance
    balance=Balance(money)
    balance.set_balance()


def changeTicker(ticker):
    msg="We're inside of change ticker " + ticker
    escribirlog(msg)
    # adjust lvg
    lvg=cambiarleverage(ticker,20)
    # get data
    losDatos = datosEx(ticker, lvg)
    dicto = {
        'ticker': ticker,
        'precision': losDatos['precision'],
        'presCant': losDatos['presCant'],
        'quoteAsset':losDatos['quoteAsset'],
        'entrada': losDatos['entrada'],
        'cantidadMinima': losDatos['cantidadMinima'],
        'minMoney':losDatos['minimoNot'],
        'leverage': lvg,
    }
    escribirDic(path+"ticker.txt",dicto)
    msj="update ticker.txt"
    escribirlog(msj)
    # ahora config
    # hay que sacar el % de entrada
    rel=20/lvg
    porcIn=rel*data.porcentajeentrada
    # saco el dicto
    dicto={
        'ticker':ticker,
        'sl':0.0125,  # por el momento sólo habrá este valor
        'porcIn':porcIn,
        'cambiar':False,
    }
    escribirDic(path+"config.txt",dicto)
    msj="update config.txt"
    escribirlog(msj)
    # es todo amigos, sólo informar y ya
    msj="we change succesfully da ticker data"
    escribirlog(msj)

@print_func_text
def getRealDeal(ticker):
    from orders import Order
    # maybe the order appears after a few seconds, because in real time mode data don't appear
    time.sleep(5)  # just for precaution
    order=Order(ticker=ticker)
    myOrder = order.read_order()[ticker]
    smb = ticker
    # to get exactly profit must see the comission, funding fee and PNL
    dateIn = myOrder['dateIn']
    dateOut = myOrder['dateOut']
    dateIn -= 5  # rest 5 scs to be sure about the info
    dateIn *= 1000  # need it in ms
    dateOut += 5  # add 5 scs to be sure about the info
    dateOut *= 1000  # need it in ms
    dateIn, dateOut = int(dateIn), int(dateOut)
    # print data to be sure of that
    msg="dateIn, dateOut and simbol  are " + str(dateIn) + ", " + str(dateOut) + ", " + smb
    escribirlog(msg)
    try:
        data = cliente.futures_income_history(startTime=dateIn, endTime=dateOut, symbol=smb)
    except:
        data=[]
    if len(data)==0:
        msg="data has no records "
        escribirlog(msg)
        return False
    df=pd.DataFrame(data)
    df['income']=df['income'].astype('float')
    profit=df['income'].sum()
    commission=df.loc[df['incomeType']=='COMMISSION']['income'].sum()
    funding = df.loc[df['incomeType'] == 'FUNDING_FEE']['income'].sum()
    pnl = df.loc[df['incomeType'] == 'REALIZED_PNL']['income'].sum()
    operations = df.loc[df['incomeType'] == 'REALIZED_PNL']['income'].count()
    ret={
        'symbol':smb,
        'dateIn':dateIn,
        'dateOut':dateOut,
        'profit':profit,
        'commission':commission,
        'funding':funding,
        'pnl':pnl,
        'operations': operations,
    }
    return  ret

@print_func_text
def datosSalida(ticker,ganancia,resultado):
    from orders import Order
    from tickers import Ticker
    from functions_orders import Balance
    msg=f'ext data have the values ticker {ticker} profit {ganancia} outcome {resultado}'
    escribirlog(msg)
    # qty and originPrice is in order
    order=Order(ticker=ticker)
    data_order=order.read_order()[ticker]
    qty=data_order['qty']
    price_in=data_order['priceIn']
    lana=ganancia*qty*price_in
    msj=f"the profit in money is {lana:.2f} "
    escribirlog(msj)
    # money get's the own balance record
    local_balance=float(Archivo(path+"balance.txt"))
    msg=f'preview local balance is {local_balance}'
    escribirlog(msg)
    new_local_balance=local_balance+lana
    msg=f'new local balance is {new_local_balance}'
    escribirlog(msg)
    updateLocalBalance(new_local_balance)
    saldo=float(Archivo(data.pathGan+"balance.txt"))
    msg=f'preview master balance is {saldo}'
    escribirlog(msg)
    saldo+=lana
    cambiarSaldo(saldo)
    msg=f'new master balance is {saldo}'
    escribirlog(msg)
    # now we need to restore the avalaible balance
    balance=Balance(saldo)
    balance.set_balance()
    saldoCta=obtenerSaldo()
    # ok the accounts doesn't look to check, in balance lose more money than the calculations, so that's wy i'm
    # beggining a new function, to look (check) the real trade, and compare with the calculate trade, and then
    # make it necesaries adjusts for the future BT (init feb 2024)
    real = getRealDeal(ticker)
    msg = "the real file is " + str(real)
    escribirlog(msg)
    if real == False:  # data has no records
        real = {
            'profit': False,
            'pnl': False,
            'commission': False,
            'funding': False,
            'operations':False,
        }
    side=data_order['side']
    qty=data_order['qty']
    dateIn=data_order['dateIn']
    dateOut=data_order['dateOut']
    priceOut=data_order['priceOut']
    profit=ganancia
    # new data is ticker,side,qty,dateIn,priceIn,dateOut,priceOut,profit,real,pnl,commission,funding,fileBalance,balance
    salida=ticker,side,resultado,qty,dateIn,price_in,dateOut,priceOut,profit,lana,real['profit'],real['pnl'],real['commission'],real['funding'], real['operations'],saldo,new_local_balance,saldoCta
    agregardatoscsv(path+"entries.csv",salida)
    # informamos al usuario
    msj=f"We realized da Exit function, the balance in file is {saldo:.2f} and the local balance is {new_local_balance:.2f}  and balance account is {saldoCta:.2f} "
    escribirlog(msj)
    # enviamos el correo
    msj=f"We realized da Exit function, the outcome is {resultado} exit data are {salida}"
    escribirlog(msj)
    miMail(msj)
    # finally we must remove from the orders and ticker, the ticker
    msg=f'debugging order, actual order value is {order.read_order()}'
    escribirlog(msg)
    order=Order(ticker=ticker)
    order.del_order()
    tk=Ticker(ticker=ticker)
    msg = f'debugging ticker, actual ticker value is {tk.read_ticker()}'
    escribirlog(msg)
    tk.del_ticker()


def salidaDeEmergencia():
    '''
    esta función se usa si se triggea inmediatamente el sl
    lo que hace es sacar los datos de la order.txt y mandar la contra a mercado, avisar al usuario y mandar datosdesalida para los registros y salida del sistema
    '''
    from functions_orders import checarOrden
    posicionSalida=""
    miArch=open(path+"order.txt")
    eldato=miArch.read()
    miArch.close()
    misdatos=leerDic(path+"ticker.txt")
    moneda=misdatos['ticker']
    #paso no. 1 sacamos la posicion y cantidad de la order.txt
    eldato=int(eldato)
    miorden=checarOrden(moneda,eldato)
    cantidad=miorden[0]
    posicion=miorden[2]
    if posicion=="BUY":
        posicionSalida="SELL"
    elif posicion=="SELL":
        posicionSalida="BUY"
    msj="se va a mandar una salida de emergencia, con posicion " + posicionSalida + " de " + str(cantidad) + " "
    escribirlog(msj)
    from functions_orders import mandarOrdenMercado
    orden=mandarOrdenMercado(moneda,posicionSalida,cantidad)
    msj="se mando cerrar con exito la orden, la id es " + str(orden) + " "
    escribirlog(msj)

def checarParcial():
    from functions_orders import checarOrden
    misdatos=leerDic(path+"ticker.txt")
    moneda=misdatos['ticker']
    miArch=open("ordenes.txt","r")
    eldato=miArch.read()
    miArch.close()
    eldato.split()
    eldato.split(",")
    #la orden 0 es la TP y la orden SL es la 1
    ordenTP=int(eldato[0])
    laorden=checarOrden(moneda,ordenTP)
    status=laorden[4]
    if status=="PARTIALLY_FILLED":
        salida=True  #además mandamos la cantidad
        cantidad=laorden[0]-laorden[6]
    else:
        salida=False
        cantidad=0
    dato=salida,cantidad
    return dato

