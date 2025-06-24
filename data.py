from pathlib import Path

# Get the current directory (which is the strategy folder)
current_dir = Path(__file__).resolve().parent

# Reference the parent directory of the current strategy folder
parent_dir = current_dir.parent

# variables and another stuf
entrada = 0.6   # ths is the minimum qty of money to use
autoentrada = True
porcentajeentrada = 0.075  # Ojo es 0.0492 en 25x pero para que no falle el
# minimal notional lo ponemos en 6%
leverage = 20

timeframe = 3  # esta variable controla cada cuanto se checan las órdenes
slmax = 0.1   # esta variable controla la pérdida máxima
tp = 0.1
sl = 0.01

path = current_dir
pathGan = str(parent_dir) + "/"

sistema = "volAcum "
usuario = " ingega "
bahia = 1
bahias = 3  # este controla el ajuste del saldoO

pausa = 10  # son los segundos que el sistema necesita para no empalmar
# las lecturas de simula.py

barras = 1440   # son los minutos que hacen que el sistema se vaya  a empate

debug_mode = False

# parameters necessary for strategy
# gap=0.03
# distance=0.015
forbidden_hour = 12
bet = 0.03
time = 10  # this is for prevent loops in everytime()
bars = 30
n = 0

# config for time
hours = 1  # 1 raise zero in preview
minutes = 1  # 1 raise zero in preview
seconds = 40

# config for review()
review_hour = 3
review_minute = 59
review_second = 0

interval = "4h"
bet_continue = True  # the bet ends until there's n bars without a sl
reverse = False  # in this system is doesn't matter because is double bet
