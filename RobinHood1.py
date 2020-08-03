from threading import Thread
import multiprocessing
import time
import robin_stocks
import math
import pdb
from urllib3.exceptions import ProtocolError

file = open('data.txt', mode='r')
data = []
for line in file:
    if line.strip('\n') == 'True':
        data.append(True)
    if line.strip('\n') == 'False':
        data.append(False)
    if line.strip('\n') == '-1':
        data.append(None)
    else:
        data.append(line.strip('\n'))

sell_price = data[0]
buy_price = data[1]
have_doge = data[2]
quantity = data[3]
file.close()

robin_stocks.authentication.login('username', 'password')


def setup():
    global quantity, buy_price
    quantity = float(robin_stocks.crypto.get_crypto_positions('quantity_available')[0])
    print("Quantity available: " + str(quantity))
    if quantity > 0.0:
        buy_price = float(robin_stocks.orders.get_all_crypto_orders()[0]['price'])
        sell_mode()
    else:
        buy_mode()


def buy_mode():
    global buy_price, have_doge, sell_price, quantity
    old_created = (robin_stocks.orders.get_all_crypto_orders()[0]['created_at'])
    print('BUYING MODE')
    cash = (0.85 * (float(robin_stocks.profiles.load_account_profile('portfolio_cash')))).__round__(2)
    doge_price = stat_tracker.price
    amount = float(cash / doge_price).__round__()
    flag = False
    while True:
        if stat_tracker.direction == -1:
            flag = False
            continue
        elif not flag:
            flag = True
            time.sleep(1.5)
        elif flag:
            break

    print(robin_stocks.orders.order_buy_crypto_by_quantity('DOGE', amount, 'mark_price'))
    print('order placed')
    time.sleep(0.5)
    print('checking for transaction')
    flag = False
    while True:
        trades = robin_stocks.orders.get_all_crypto_orders()[0]
        if trades['created_at'] != old_created:
            if not flag:
                flag = True
                print('found transaction. will alert when purchase confirmed.')

            if trades['state'] == 'filled':
                average = trades['average_price']
                buy_price = float(average)
                print("Purchased " + str(cash * 0.9) + " worth of Doge coin at " + str(average)
                      + " per coin")
                have_doge = True
                save_data(sell_price, buy_price, have_doge, quantity)
                sell_mode()

            doge_price = float(robin_stocks.crypto.get_crypto_quote("DOGE")['mark_price'])

            if (doge_price - float(trades['price'])) >= 0.00002 or \
                    (doge_price - float(trades['price'])) <= -0.00002:
                robin_stocks.cancel_all_crypto_orders()
                print("Price change. Order has been canceled. Trying again")
                buy_mode()


def sell_mode():
    global buy_price, have_doge, sell_price, quantity

    old_created = (robin_stocks.orders.get_all_crypto_orders()[0]['created_at'])
    quantity = robin_stocks.crypto.get_crypto_positions('quantity_available')[0]
    doge_price = stat_tracker.price
    while True:
        if stat_tracker.price > float(buy_price):
            if (stat_tracker.price - buy_price) >= 0.000005:
                set_speed = stat_tracker.true_speed
                while True:
                    if stat_tracker.true_speed > set_speed:
                        set_speed = stat_tracker.true_speed
                    if stat_tracker.true_speed + stat_tracker.true_speed <= set_speed:
                        break
                    else:
                        print('Price still rising, waiting to sell. True speed = ' + str(stat_tracker.true_speed))
                        continue

                print(robin_stocks.orders.order_sell_crypto_by_quantity("DOGE", quantity, 'mark_price'))
                print('sell order placed')
                time.sleep(0.4)
                print('checking for transaction')
                flag = False

                while True:
                    trades = robin_stocks.orders.get_all_crypto_orders()[0]
                    if trades['created_at'] != old_created:
                        if not flag:
                            flag = True
                            print('found transaction. will alert when purchase confirmed.')

                        if trades['state'] == 'filled':
                            sell_price = trades['average_price']
                            quantity = trades['quantity']
                            print(str(quantity) + " DOGE coins sold at market price " + str(doge_price))
                            save_data(sell_price, buy_price, have_doge, quantity)
                            buy_mode()

                        doge_price = float(robin_stocks.crypto.get_crypto_quote("DOGE")['mark_price'])

                        if (stat_tracker.price - float(trades['price'])) <= -0.00002:
                            robin_stocks.cancel_all_crypto_orders()
                            print("Price raised. Order has been canceled. Trying again")
                            sell_mode()
            else:
                print("SELL MODE | Doge price: " + str(doge_price) + '\t| SO CLOSE |\t' + 'Bought Doge: ' + str(
                    buy_price)
                      + " |  Price difference:  " + str((doge_price - buy_price).__round__(9)))
                time.sleep(0.4)

        else:
            print('\tSELL MODE | Price = ' + str(stat_tracker.price) + '\t\t Buy Price = ' + str(
                buy_price) + '\t\t Speed = ' +
                  str(stat_tracker.speed) + '\t\t True Speed = ' + str(stat_tracker.true_speed) + '\t\t Direction = ' + str(stat_tracker.direction))
            time.sleep(0.4)


def save_data(sell, buy, have, quan):
    file1 = open('data.txt', 'w+')
    if sell is None:
        sell = -1
    if buy is None:
        buy = -1
    if quan is None:
        quan = -1
    file1.write(str(sell) + '\n' + str(buy) + '\n' + str(have) + '\n' + str(quan))
    file1.close()


class StatTracker(object):

    def __init__(self):

        self.direction = 0
        self.speed = 0
        self.true_speed = 0
        self.last_30 = []
        self.price = 0
        self.sum = 0

        thread = Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        while True:
            price = float(robin_stocks.crypto.get_crypto_quote("DOGE")['mark_price'])
            self.last_30.insert(0, price)
            try:
                if self.last_30[60] is not None:
                    self.last_30.__delitem__(60)
            except IndexError:
                pass

            if len(self.last_30) > 1:
                if self.last_30[1] - self.last_30[0] < 0:
                    self.direction = 1
                elif self.last_30[1] - self.last_30[0] > 0:
                    self.direction = -1
                else:
                    self.direction = 0
                for x in range(len(self.last_30) - 1):
                    self.sum += (self.last_30[x + 1] - self.last_30[x])
                self.sum *= 100000
                self.speed = (self.sum / (len(self.last_30) - 1)).__round__(6)
                self.speed *= -1
                self.sum = 0
            if len(self.last_30) > 5:
                self.true_speed = (((self.last_30[0] - self.last_30[1])
                                    + (self.last_30[1] - self.last_30[2])
                                    + (self.last_30[2] - self.last_30[3])
                                    + (self.last_30[3] - self.last_30[4])
                                    + (self.last_30[4] - self.last_30[5])) / 5)
            self.price = self.last_30[0]
            time.sleep(0.3)


stat_tracker = StatTracker
while True:
    while True:
        try:
            stat_tracker = StatTracker()
            setup()
        except ConnectionError:
            print("Connection Error.")
            continue
        except ProtocolError:
            print("Protocol Error")
            continue
        except OSError:
            print("OS Error")
            continue
        except RecursionError:
            print("Recursion Error")
            continue

