# CryptoBot
Python Bot I made using RobinStocks API. This bot constantly monitors statistics on the crypto currency selected (Doge Coin currently) and then proceeds to buy and sell the currency based on the price/price-speed/direction of the crypto currency.

The class StatTracker runs itself as a seperate thread that is constantly monitering the stats of the crypto. Stats are as follows:
Price: The current market price.
Speed: The average difference between the prices for the last 20-30 seconds.
True Speed: The average difference between the prices for the last 2-3 seconds.

SELL MODE:
When the market price goes above the bot's buy price, the bot will set the set_speed = True Speed, and will continue to allow the price to rise.
When the True Speed drops to half of the set_speed, the bot will trigger the sell.

BUY MODE:
WARNING THIS BOT WILL SPEND ALL YOUR ROBIN HOOD CASH. This bot is programmed to essentially have its' own RobinHood account, as it will always buy and sell using (almost)
you max money. Use at your own risk.
The bot will watch to see if the price is falling, and if it is it will let the price fall until it levels out, and attempt to buy before the price rises again. 
