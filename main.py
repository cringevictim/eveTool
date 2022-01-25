import requests
import json
import sqlite3

debug_mode = False
semi_debug_mode = True

def get_api(type_id):
    if debug_mode:
        print("Getting api (ID " + str(type_id) + ")")
    if semi_debug_mode:
        print("Searching for (ID " + str(type_id) + ")")
    api_request = requests.get("https://evetycoon.com/api/v1/market/orders/"+str(type_id))
    api_data = json.loads(api_request.text)
    if debug_mode:
        print("Api received")
    return api_data

def fill_database(type_id, api_data):
    if debug_mode:
        print("Filling database (ID " + str(type_id) + ")")
    for object1 in api_data['orders']:
        sql.execute(f"INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)",
                    (object1['orderId'],
                     object1['typeId'],
                     object1['isBuyOrder'],
                     object1['price'],
                     object1['volumeRemain'],
                     object1['systemId'],
                     object1['locationId'],
                     api_data['systems'][str(object1['systemId'])]['security']))
    if debug_mode:
        print("Database was filled")
    return

def compress_buy_orders(id, percentage):
    if debug_mode:
        print("Compressing buy orders (ID " + str(id) + ")")
    sql.execute("SELECT station_id "
                "FROM orders "
                "WHERE is_buy_order = 1 "
                "AND type_id = " + str(id) + " "
                "GROUP BY station_id ")
    stations = sql.fetchall()
    for obj in stations:
        sql.execute("SELECT price, volume "
                    "FROM orders "
                    "WHERE is_buy_order = 1 "
                    "AND type_id = " + str(id) + " "
                    "AND volume = (SELECT MAX(volume) FROM orders WHERE is_buy_order = 1 AND type_id = " + str(id) + " AND station_id = " + str(obj[0]) +")"
                    "AND station_id = "+ str(obj[0]))
        max_volume_min_price_order = min(sql.fetchall())

        sql.execute("SELECT order_id, type_id, is_buy_order, SUM(price*volume)/SUM(volume), SUM(volume), system_id, station_id, security "
                    "FROM orders "
                    "WHERE is_buy_order = 1 "
                    "AND type_id = " + str(id) + " "
                    "AND price >= " + str(max_volume_min_price_order[0] * (1 - percentage / 100)) + " "
                    "AND price <= " + str(max_volume_min_price_order[0] * (1 + percentage / 100)) + " "
                    "AND station_id = " + str(obj[0]))
        to_paste = sql.fetchall()

        sql.execute("DELETE FROM orders "
                    "WHERE is_buy_order = 1 "
                    "AND type_id = " + str(id) + " "
                    "AND price >= " + str(max_volume_min_price_order[0]*(1-percentage/100)) + " "
                    "AND price <= " + str(max_volume_min_price_order[0]*(1+percentage/100)) + " "
                    "AND station_id = " + str(obj[0]))

        sql.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)", (
            to_paste[0][0],
            to_paste[0][1],
            to_paste[0][2],
            to_paste[0][3],
            to_paste[0][4],
            to_paste[0][5],
            to_paste[0][6],
            to_paste[0][7]))
    if debug_mode:
        print("Complete")
    return

def compress_sell_orders(id, percentage):
    if debug_mode:
        print("Compressing sell orders (ID " + str(id) + ")")
    sql.execute("SELECT station_id "
                "FROM orders "
                "WHERE is_buy_order = 0 "
                "AND type_id = " + str(id) + " "
                "GROUP BY station_id ")
    stations = sql.fetchall()
    for obj in stations:
        sql.execute("SELECT price, volume "
                    "FROM orders "
                    "WHERE is_buy_order = 0 "
                    "AND type_id = " + str(id) + " "
                    "AND volume = (SELECT MAX(volume) FROM orders WHERE is_buy_order = 0 AND type_id = " + str(id) + " AND station_id = " + str(obj[0]) +")"
                    "AND station_id = "+ str(obj[0]))
        max_volume_max_price_order = max(sql.fetchall())

        sql.execute("SELECT order_id, type_id, is_buy_order, SUM(price*volume)/SUM(volume), SUM(volume), system_id, station_id, security "
                    "FROM orders "
                    "WHERE is_buy_order = 0 "
                    "AND type_id = " + str(id) + " "
                    "AND price >= " + str(max_volume_max_price_order[0] * (1 - percentage / 100)) + " "
                    "AND price <= " + str(max_volume_max_price_order[0] * (1 + percentage / 100)) + " "
                    "AND station_id = " + str(obj[0]))
        to_paste = sql.fetchall()

        sql.execute("DELETE FROM orders "
                    "WHERE is_buy_order = 0 "
                    "AND type_id = " + str(id) + " "
                    "AND price >= " + str(max_volume_max_price_order[0]*(1-percentage/100)) + " "
                    "AND price <= " + str(max_volume_max_price_order[0]*(1+percentage/100)) + " "
                    "AND station_id = " + str(obj[0]))

        sql.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)", (
            to_paste[0][0],
            to_paste[0][1],
            to_paste[0][2],
            to_paste[0][3],
            to_paste[0][4],
            to_paste[0][5],
            to_paste[0][6],
            to_paste[0][7]))
    if debug_mode:
        print("Complete")
    return

def destination_name(id, api_data):
    if id > 70000000:
        return api_data["structureNames"][str(id)]
    else:
        return api_data["stationNames"][str(id)]

def search(id, minimal_profit, api, security):
    if debug_mode:
        print("Searching (ID " + str(id) + ")")
    sql.execute("SELECT COUNT(*) FROM orders WHERE is_buy_order = 0 AND type_id = "+str(id)+" AND security >= "+str(security))
    sell_orders = int(str(sql.fetchone()[0]))
    sql.execute("SELECT COUNT(*) FROM orders WHERE is_buy_order = 1 AND type_id = "+str(id)+" AND security >= "+str(security))
    buy_orders = int(str(sql.fetchone()[0]))
    sql.execute("SELECT * FROM orders WHERE is_buy_order = 0 AND type_id = "+str(id)+" AND security >= "+str(security))
    object1 = sql.fetchall()
    sql.execute("SELECT * FROM orders WHERE is_buy_order = 1 AND type_id = "+str(id)+" AND security >= "+str(security))
    object2 = sql.fetchall()
    counter = 0
    for counter1 in range(sell_orders):
        for counter2 in range(buy_orders):
            bp = object2[counter2][3]
            sp = object1[counter1][3]
            if sp > bp:
                continue
            volume = min(object1[counter1][4], object2[counter2][4])
            profit = int((bp-sp)*volume)
            if profit < minimal_profit:
                continue
            counter = counter + 1
            sql.execute("INSERT INTO paths VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                object1[counter1][1],
                sp,
                bp,
                volume,
                volume * api['itemType']['volume'],
                profit,
                profit/1000000,
                profit / (volume * api['itemType']['volume']),
                object1[counter1][5],
                object1[counter1][6],
                object2[counter2][5],
                object2[counter2][6],
                destination_name(object1[counter1][6], api),
                destination_name(object2[counter2][6], api)))
    if debug_mode:
        print("Matches (ID " + str(id) + "): " + str(counter))
        print("Complete")
    return

db = sqlite3.connect('orders.db')
sql = db.cursor()

if True:
    sql.execute("DROP TABLE IF EXISTS paths")
if True:
    sql.execute("DROP TABLE IF EXISTS orders")

sql.execute("""CREATE TABLE IF NOT EXISTS orders (
    order_id INT,
    type_id INT,
    is_buy_order INT,
    price FLOAT,
    volume BIGINT,
    system_id BIGINT,
    station_id BIGINT,
    security)""")

sql.execute("""CREATE TABLE IF NOT EXISTS paths (
    type_id INT,
    sell_price FLOAT,
    buy_price FLOAT,
    amount BIGINT,
    volume BIGINT,
    profit BIGINT,
    mil_profit INT,
    isk_per_m3 FLOAT,
    starting_system_id BIGINT,
    starting_station_id BIGINT,
    ending_system_id BIGINT,
    ending_station_id BIGINT,
    starting_station_name STRING,
    ending_station_name STRING)""")

array = {34, 35, 36, 37, 38, 39, 40}

for id in range(30000):#12075 поставь фолс на очистку
    api = get_api(id)
    fill_database(id, api)
    compress_buy_orders(id, 5)
    compress_sell_orders(id, 5)
    search(id, 30_000_000, api, 0.5)
    if id % 25 == 0:
        print("Database was committed")
        db.commit()
db.commit()
if debug_mode:
    print("Database was committed")