# -*- coding: utf-8 -*-
"""
Created on Sun Jun 17 08:45:08 2018

@author: tpreusch
"""
# API Headers
import warnings, smtplib, time, cbpro, pymongo, numpy, pandas, sklearn.linear_model as lm, math, datetime

from coinbase.wallet.client import Client

warnings.simplefilter(action='ignore', category=FutureWarning)

error = True

public_client = cbpro.PublicClient()

def db_start_up(i):
    # Future line for dynamic size update db.runCommand({"convertToCapped": "log", size: 1000000000});
    client = pymongo.MongoClient()
    db = client.trading
    # db.drop_collection(i)
    # db.create_collection(i)
    print("We are in DB Start Up")
    print(db[i])
    dbnames = cbpro.WebsocketClient(url="wss://ws-feed.pro.coinbase.com", products=i,
                                       channels=["matches"], mongo_collection=db[i], should_print=False)
    dbnames.start()
    return dbnames, db

def SocketToMe(name):
    name.start()

def sendemail(from_addr='tpreusch@gmail.com', to_addr_list=['soprisanalyticsbitcoin1@gmail.com'], subject='hello', message='yay',
              login='tpreusch@gmail.com', password='######',
              smtpserver='smtp.gmail.com:587'):
    header = 'From: %s\n' % from_addr
    header += 'To: %s\n' % ','.join(to_addr_list)
    header += 'Subject: %s\n\n' % subject
    message = header + message

    server = smtplib.SMTP(smtpserver)
    server.starttls()
    server.login(login, password)
    problems = server.sendmail(from_addr, to_addr_list, message)
    server.quit()
    return problems

def login():
    # GDAX Public Client

    # Coinbase CLient
    client = Client('##########', '##########')

    # GDAX Connection Details
    from requests.auth import AuthBase

    api_base = 'https://api.pro.coinbase.com'
    api_key = '##########'
    api_secret = '##########'
    passphrase = '##########'
    secret_key = '##########'
    auth_client = cbpro.AuthenticatedClient(api_key, api_secret, passphrase
                                           , api_url="https://api.pro.coinbase.com")

    return auth_client



def tradeAnalysis(account):
    Fills = account.get_fills(product_id="BTC-USD")
    # print(Fills)
    i = 0
    db.Fills.delete_many({})
    while i < 100:
        db.Fills.insert_one({'created_at': Fills[0][i].get('created_at'), 'trade_id': Fills[0][i].get('trade_id'),
                             'product_id': Fills[0][i].get('product_id'), 'price': Fills[0][i].get('price'),
                             'fee': Fills[0][i].get('fee'), 'side': Fills[0][i].get('side'),
                             'size': Fills[0][i].get('size')})
        i = i + 1

    print(account)

# ____________________________________Trading Functions_________________________________________
def truncate(n, decimals):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier

def buy(trade, product, size, auth_client, dollarAccount):
    print("BUY")
    print(trade * size)
    print(numpy.log10(1/size))
    x = int(numpy.log10(1 / size))
    y = truncate(dollarAccount/trade, x)
    if y > size:
        BUY = auth_client.buy(
            order_type = 'market',
            price = round(float(trade), 2),  # USD
            size = y,  # BTC
            product_id = product)
        print(BUY)
        sendemail(subject='buy', message=str(BUY))


def sell(trade, product, size, auth_client, dollarAccount, sellQuantity):
    print('Sell')
    print(product)
    print(sellQuantity)
    print(dollarAccount)
    print(numpy.log10(1 / size))
    x = int(numpy.log10(1 / size))
    print(truncate(float(sellQuantity), x))
    SELL = auth_client.sell(
        order_type='market',
        # post_only=True,
        price=round(float(trade), 2),  # USD
        size=truncate(float(sellQuantity), x),  # BTC
        product_id=product)
    print(SELL)
    sendemail(subject='Sell', message=str(SELL))

# _____________  _______________________Trading Functions_________________________________________

def trading_decision(database):
    x = []
    y = []
    z = []
    c = []
    q = 0

    for doc in database.find({}):
        t = doc.get('price')
        u = doc.get('_id')
        s = doc.get('time')
        d = doc.get('product_id')
        r = doc.get('time')
        l = doc.get('side')
        j = doc.get('type')
        if j == 'subscriptions':
            q = q+1
        else:
            s = s.replace('T', '')
            s = s.replace('-', '')
            s = s.replace(':', '')
            s = s.replace('Z', '')

            t = float(t)
            s = float(s)

            y.append(t)
            x.append(s)
            c.append(l)
            z.append(r)

    # Linear Prediction
    data = pandas.DataFrame({'x': x, 'y': y, 'c': c})

    # buydata = data[(data.c == 'buy')]
    # selldata = data[(data.c == 'sell')]
    print('Amount of rows')
    print(len(data))
    if len(data) > 100:
        length_array = len(y)

        if length_array < 100:
            limit = length_array
        else:
            limit = 100

        time_range = x[length_array - 1] - x[0]
        latest_value = x[length_array - 1] - 1000
        x = numpy.array(x)
        index = (numpy.abs(x - latest_value)).argmin()
        data = data.iloc[0:limit]
        model2 = lm.LinearRegression().fit(data[['x', 'y']], data['y'])

        predictions = model2.predict(data[['x', 'y']])

        plength = len(predictions)

        pchange = predictions[plength - 1] - predictions[0]
        # print('Predictions')
        # print(predictions[plength - 1])
        # print(predictions[0])
        pchange = pchange/predictions[0]

        # Plotting

        # print('Time Range')
        # print([x[length_array - 1], x[0]])
        # print(time_range)
        # print('normalized movement')
        timeNormal = pchange/time_range*1000000
        # print(timeNormal)

        l = numpy.array(y, dtype=numpy.float)

        return [timeNormal]


def main(auth_client,account):
    public_client = cbpro.PublicClient()
    productInformation = public_client.get_products()
    print(productInformation)
    time.sleep(1)

    currency = []
    tradeables = []

    size = []
    for i in productInformation:
        if i.get('quote_currency') == 'USD':
            if i.get('base_currency') != 'DASH' and i.get('base_currency') != 'ALGO'and i.get('base_currency') != 'XTZ':
                tradeables.append(i.get('id'))
                currency.append(i.get('base_currency'))
                size.append(float(i.get('base_min_size')))
                print(tradeables)
                print(currency)

    websocket = []
    j = 0
    for i in tradeables:
        time.sleep(1)
        webs, db = db_start_up(i)
        websocket.append(webs)
        # print("Creating WebSockets")
        # print(webs)
        j += 1

    j = 0
    #while j < 3:
    #    time.sleep(30)
    for i in websocket:
        # print(i)
        if i.stop:
            # print("Checking Connection")
            # print(i.stop)
            i.close()
            i.start()

    # for i in tradeables:
    #     print("Starting the DBs")
    #     print(db.i.count())
    #     if db[i].count() == 0:
    #         db_start_up(i)

    j += 1

    time.sleep(1)
#======================================================================================================================
    for t in range(10000):
        time.sleep(10)
        account = auth_client.get_accounts()
        print(account)
        #
        # for i in tradeables:
        #     print(db.i.count())
        #     if db.i.count() == 0:
        #         print("Empty DB Restarting")
        #         db_start_up(i)

        for i in websocket:
            if i.stop:
                print("websocket Down")
                i.close()
                i.start()

        availableArray = []
        for j in currency:
            # print(j)
            for i in account:
                if i.get('currency') == j:
                    availableArray.append(float(i.get('available')))
                if i.get('currency') == 'USD':
                    dollarAccount = float(i.get('available'))

        # BUY ARRAY
        buyArray = []
        sellArray = []
        ccPair = []
        sizeArray = []
        sellccPair = []
        sellsizeArray = []
        sellavailable = []
        j = 0

        while j < len(tradeables):
            database = db[tradeables[j]]
            x = trading_decision(database)
            if x is not None:
                buyArray.append(x[0])
            else:
                buyArray.append(0)
            ccPair.append(tradeables[j])
            if availableArray[j] >= size[j]:
                if x is not None:
                    sellArray.append(x[0])
                else:
                    sellArray.append(0)
                sellccPair.append(tradeables[j])
                sellsizeArray.append(size[j])
                sellavailable.append(availableArray[j])
            print(x)
            j += 1

        print("Array")
        print(tradeables)
        print(ccPair)
        print(buyArray)
        i = 0
        regressiontable = {}
        while i < len(buyArray):
            regressiontable.update({tradeables[i]: buyArray[i]})
            i += 1
        regressiontable.update({'time': datetime.datetime.now()})
        db.regression.insert_one(regressiontable)
        print(sellccPair)
        print(sellArray)
        print("Max")
        print(numpy.max(buyArray))
        buyCCY = numpy.max(buyArray)
        buyCCY_Index = buyArray.index(buyCCY)
        buyProduct = ccPair[buyCCY_Index]
        buySize = size[buyCCY_Index]

        print("sum")
        print(numpy.sum(buyArray))
        sumBuy = numpy.sum(buyArray)
        print("dollars")
        print(dollarAccount)

        if buyCCY > 0 and dollarAccount > 20 and sumBuy > 0:
            print('Buying Coin with USD')
            product = buyProduct
            public_client = cbpro.PublicClient()
            go = public_client.get_product_order_book(product)
            print(go)
            trade = float(go.get('bids')[0][0])
            buy(trade, product, buySize, auth_client, dollarAccount)
            print(trade)

        print("Min")
        if len(sellArray) != 0:
            print(numpy.min(sellArray))
            sellCCY = numpy.min(sellArray)
            sellCCY_Index = sellArray.index(sellCCY)
            sellProduct = sellccPair[sellCCY_Index]
            sellSize = sellsizeArray[sellCCY_Index]
            sellQuantity = sellavailable[sellCCY_Index]

            if sellCCY < 0 or sumBuy < 0 or sellCCY < buyCCY:
                print('Selling Coin for USD')
                product = sellProduct
                public_client = cbpro.PublicClient()
                go = public_client.get_product_order_book(product)
                print(go)
                trade = float(go.get('bids')[0][0])
                sell(trade, product, sellSize, auth_client, dollarAccount,sellQuantity)
                print(trade)

        if t % 100 == 0:
            sendemail(subject='Alive', message=str(t))

        print(t)
print("Initiating Pennies__________________________________________________________________")
auth_client = login()
account = auth_client.get_accounts()
main(auth_client,account)
while error:
    try:
        print("Initiating Pennies__________________________________________________________________")
        sendemail(subject='Broken', message='Restart')
        time.sleep(1800)
        auth_client = login()
        main(auth_client,account)
        error = False
    except:
        error = True
