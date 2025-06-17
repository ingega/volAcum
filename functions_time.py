import time
from data import hours


def cada55():
    # la idea de esta función es sacar el dato a cinco segundos del minuto
    yasalio = False
    while True:
        #le ponemos una pausa de 1 seg iniciando para que no entre doble
        time.sleep(1)
        a=time.localtime()[5]
        if a>=50 and yasalio==False: # van 55 segundos, nos vamos cada medio segundo
            while True:
                a=time.localtime()[5]
                if a==55:
                    yasalio=True
                    break
                else:
                    time.sleep(0.1)
        else:
            time.sleep(1)
        if yasalio == True:
            break

def cada28():
    # la idea de esta función es sacar el dato a cinco segundos del minuto
    yasalio = False
    while True:
        #le ponemos una pausa de 1 seg iniciando para que no entre doble
        time.sleep(1)
        a=time.localtime()[5]
        if a>=20 and yasalio==False: # van 55 segundos, nos vamos cada medio segundo
            while True:
                a=time.localtime()[5]
                if a==28:
                    yasalio=True
                    break
                else:
                    time.sleep(0.1)
        else:
            time.sleep(1)
        if yasalio == True:
            break

def every15m():
    #this function executed every hour
    # y,m,d,h,min,sec
    time.sleep(20)  # avoid loop
    while True:
        minutes=time.gmtime().tm_min
        minutes%=15
        if minutes==14:
            cada55()
            break
        else:
            time.sleep(25)  # to reach da 58 secs function

def everyHour():
    #this function executed every hour
    # y,m,d,h,min,sec
    time.sleep(20)  # avoid loop
    while True:
        minutes=time.gmtime().tm_min
        if minutes==57:  # we need several minutes to look the entries
            cada55()
            break
        else:
            time.sleep(40)  # to reach da 58 secs function

def everyFourHours():
    #this function executed every 4 hour
    # y,m,d,h,min,sec
    time.sleep(20)  # avoid loop
    while True:
        hours=time.gmtime().tm_hour
        hours%=4
        if hours==3:
            everyHour()
            break
        else:
            time.sleep(60*40)  # in order to check every 40 minutes

def everyDay():
    # this function executed every day at datos.hour hours-1 (because end almost in hour)
    # y,m,d,h,min,sec
    time.sleep(20)  # avoid loop
    while True:
        hour = time.gmtime().tm_hour
        if hour == hours - 1:
            everyHour()
            break
        else:
            time.sleep(60 * 40)  # in order to check every 40 minutes

def every_time(hrs=0, mins=0, secs=0):
    while True:
        # we need a pause in order to avoid looping
        time.sleep(10)
        if hrs > 0:
            # if mins and secs are no set, send an error
            if mins * secs == 0:
                print(f'mins and secs must be set')
                return
            while True:
                hour = time.gmtime().tm_hour
                hour %= hrs
                if hour == hrs - 1:
                    break
                else:
                    time.sleep(2400)  # 40 mins
        if mins > 0:
            if secs == 0:
                print(" secs must be set ")
                return
            while True:
                minutes = time.gmtime().tm_min
                minutes %= mins
                if minutes == mins -1:
                    break
                else:
                    time.sleep(20)
        while True:
            seconds = time.gmtime().tm_sec
            if seconds >= secs-10:  # van 55 segundos, nos vamos cada medio segundo
                while True:
                    a = time.gmtime().tm_sec
                    if a == secs:
                        return
                    else:
                        time.sleep(0.1)
            else:
                time.sleep(1)
