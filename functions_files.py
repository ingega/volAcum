from data import path
import time, ast, csv, math
from csv import reader


def escribirlog(mensaje):
    miarch=open(path +"log.txt","a")
    msj=mensaje + " " + time.asctime(time.gmtime()) + "\n"
    miarch.write(msj)
    miarch.close()
    print(msj)

def escribirDic(archivo,dic):
    midato=str(dic)
    miArch=open(archivo,"w")
    miArch.write(midato)
    miArch.close()
    msj="se escribieron correctamente los valores " + midato + " en " + archivo
    escribirlog(msj)

def leerDic(archivo):
    #esta función abre un txt, y lo pasa a un diccionario
    #si no es diccionario va a mandar un error que dice que esta malformado el diccionario
    # debido a que AST requiere algún dato, checamos que no esté vacio el archivo
    salida={}
    dato=Archivo(archivo)
    if len(dato)<4: # ni al caso
        msj="No contiene info el archivo " + archivo
        escribirlog(msj)
    else:
        salida=ast.literal_eval(dato)
    return salida

def agregardatoscsv(nombrearchivo, dato):
    with open(nombrearchivo, 'a', newline='') as csvfile:
        linea = csv.writer(csvfile, delimiter=',')
        try:
            linea.writerow(dato)  # los datos que necesites
        except:
            print("no se pudo agregar el dato ",dato)

def abrircsv(archivo):
    with open(archivo, 'r') as csv_file:
        csv_reader = reader(csv_file)
        # Passing the cav_reader object to list() to get a list of lists
        salida = list(csv_reader)
    return salida

def datosEx(moneda, lvg):
    from functions import cliente
    salida={}
    precio=float(cliente.futures_recent_trades(symbol=moneda,limit=1)[0]['price'])
    ex=cliente.futures_exchange_info()
    simbolos=ex['symbols']
    for a in simbolos:
        if a ['symbol']==moneda:
            presCan=a['quantityPrecision']
            celfloor=a['marketTakeBound']
            quoteAsset=a['quoteAsset']
            filtros=a['filters']
            pres=float(filtros[0]['tickSize'])
            preci=round(math.log(1/pres,10))
            minimo = float(filtros[5]['notional'])  # ok this is the minum qty in dolars to buy
            minimo = int(minimo)
            entradamin=precio/(10**presCan)
            entrada=entradamin/lvg
            if entrada<minimo/lvg:
                entrada=minimo/lvg
            cantidadminima=filtros[2]['minQty']
            salida={
                'ticker':moneda,
                'precision':preci,
                'presCant':presCan,
                'minimoNot':minimo,
                'quoteAsset':quoteAsset,
                'entrada':entrada,
                'celfloor':float(celfloor),
                'cantidadMinima':float(cantidadminima),
            }
    return salida

def escribirerror(mensaje,codigo):
    miarch=open(path +"errorlog.txt","a")
    strcode=str(codigo)
    msj="la API de binance cometio un error consistente en " + mensaje + " error no. " + strcode + " hora local: " + time.ctime() + "\n"
    miarch.write(msj)
    miarch.close()
    print(msj)

def Archivo(archivo):
    miArch=open(archivo,"r")
    eldato=miArch.read()
    miArch.close()
    return eldato