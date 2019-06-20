#!/usr/bin/env python
"""
Very simple HTTP server in python.
Usage::
    ./dummy-web-server.py [<port>]
Send a GET request::
    curl http://localhost
Send a HEAD request::
    curl -I http://localhost
Send a POST request::
    curl -d "foo=bar&bin=baz" http://localhost
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import base64
import sqlite3
import numpy
from itertools import chain


def build_action_refill(where, what):
    text = "<action>\n"
    text += "<type>refill</type>\n"
    text += "<where>" + where + "</where>\n"
    text += "<what>" + base64.b64encode(bytes(what, 'utf-8')).decode('ascii') + "</what>\n"
    text += "</action>\n"
    return text


def build_action_append(where, what):
    text = "<action>\n"
    text += "<type>append</type>\n"
    text += "<where>" + where + "</where>\n"
    text += "<what>" + base64.b64encode(bytes(what, 'utf-8')).decode('ascii') + "</what>\n"
    text += "</action>\n"
    return text


def build_action_total(value):
    text = "<action>\n"
    text += "<type>total</type>\n"
    text += "<value>" + str(value) + "</value>\n"
    text += "</action>\n"
    return text


def build_action_reset():
    text = "<action>\n"
    text += "<type>reset</type>\n"
    text += "</action>\n"
    return text   

def build_action_status():
    text = "<action>\n"
    text += "<type>status</type>\n"
    text += "</action>\n"
    return text    

class S(BaseHTTPRequestHandler):

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html'.encode("utf-8"))
        self.end_headers()

    def do_GET(self):

        parts = self.path.split("?", 1)


        if self.path == '/':
            self.send_response(200)
            fname = 'till.html'
            file = open(fname, "r")
            text = file.read()
            self.send_header('Content-type', 'text/html')
        elif self.path == '/till.css':
            self.send_response(200)                                         # Moved on top of elif block
            fname = 'till.css'
            file = open(fname, "r")
            text = file.read()
            self.send_header('Content-type', 'text/css')
        elif self.path == '/till2.html':
            self.send_response(200)
            fname = 'till2.html'
            file = open(fname, "r")
            text = file.read()
            self.send_header('Content-type', 'text/html')
        elif self.path == '/till.js':
            self.send_response(200)
            fname = 'till.js'
            file = open(fname, "r")
            text = file.read()
            self.send_header('Content-type', 'application/javascript')
        elif parts[0] == '/action':
            self.send_response(200)

            subtext = ""
            for p in parts[1].split("&"):                                   # Splits request url into two halves using & as separator
                subtext = subtext + p + "<br>"

            action = (parts[1].split("&")[0]).split("=")[1]                 # Splits LHS of request url into two halves using = as separator

            if action == 'plu':
                refund = 0                                                  # Parameters
                num = 0
                plu = 0
                for p in parts[1].split("&"):                               # Split using &
                    sp = p.split("=")
                    if (sp[0] == 'refund'):
                        refund = sp[1]                                      # Feeds parameter value to local variable
                    if (sp[0] == 'num'):
                        num = sp[1]    
                    if (sp[0] == 'plu'):
                        plu = sp[1] 

                text = '<?xml version="1.0" encoding="UTF-8"?>\n'
                text += "<response>\n"
                text += build_action_total(200)      

                db = sqlite3.connect('products.db')                         # Creates connection to database
                cursor = db.cursor()                                        # Cursor object

                cursor.execute("""SELECT productid, name, shift, price FROM products WHERE plu=?;""",[plu]) # SELECT query
                product_results = cursor.fetchone()
                
                if product_results is not None:                             # If list not empty
                    product = product_results
                
                    cursor.execute("""SELECT transactionid FROM transactions WHERE status = '0';""") # Find current transaction
                    transactionid = cursor.fetchone()
                
                    if transactionid is None:                               # If no transaction in progress
                        print('inserting new transaction...')
                        cursor.execute("""INSERT into transactions (timestamp, transactiontype, status) VALUES (CURRENT_TIMESTAMP,?,?);""",[refund, 0]) # Create new one
                
                    else:
                        cursor.execute("""INSERT into items (timestamp, transactionid, productid) VALUES (CURRENT_TIMESTAMP,(SELECT transactionid FROM 'transactions' WHERE status = '0'),?);""",[product[0]]) # INSERT product

                    db.commit()                                             # Commit changes
                    db.close()                                              # Close connection

                    t = str(product[1]) + " x " + str(num) + "<br>"          # displays 'product x num' on till display 
                    text += build_action_append("target", t)  
                    text += build_action_refill("title", "Transaction in progress...")
                    text += build_action_total(product[3])
                    text += "</response>\n"
                    self.send_header('Content-type', 'application/xml') 

                else:
                    text = '<?xml version="1.0" encoding="UTF-8"?>\n'
                    text += "<response>\n"
                    text += build_action_total(200) 
                    text += build_action_append("target", "Plu ID not found.")  
                    text += build_action_refill("title", "Transaction cannot go through")
                    text += build_action_total(200)
                    text += "</response>\n"
                    self.send_header('Content-type', 'application/xml')                     

            if action == 'program':
                refund = 0                                              # Parameters
                num = 0
                pos = 0
                shift = 0
                value = 0
                for p in parts[1].split("&"):
                    sp = p.split("=")
                    if (sp[0] == 'refund'):
                        refund = sp[1]
                    if (sp[0] == 'num'):
                        num = sp[1]    
                    if (sp[0] == 'pos'):
                        pos = sp[1]
                    if (sp[0] == 'shift'):
                        shift = sp[1]
                    if (sp[0] == 'value'):
                        value = sp[1]

                text = '<?xml version="1.0" encoding="UTF-8"?>\n'
                text += "<response>\n"
                text += build_action_total(200)      

                db = sqlite3.connect('products.db')
                cursor = db.cursor()

                cursor.execute("""SELECT productid, name, shift, price FROM products where pos=?;""",[pos])
                product_results = cursor.fetchall()                                                            # Fetches all products with same pos value

                product =[]
                size = ""

                # Finds the correct size of drink to be displayed and inserted in the database
                if shift=="1":
                    product = product_results[0]
                    size = "Small"
                elif shift=="2":
                    product = product_results[1]
                    size = "Medium"   
                elif shift=="3" and len(product_results)==1:
                    product = product_results[0]  
                elif shift=="3":
                    product = product_results[2] 
                    size = "Large"   
                else:     
                    product = product_results[0]
                print(product)    
            
                
                cursor.execute("""SELECT transactionid FROM transactions WHERE status = '0';""")
                transactionid = cursor.fetchone()

                if transactionid is None:
                    print('inserting new transaction...')
                    cursor.execute("""INSERT into transactions (timestamp, transactiontype, status) VALUES (CURRENT_TIMESTAMP,?,?);""",[refund, 0])
                
                else:
                    cursor.execute("""INSERT into items (timestamp, transactionid, productid) VALUES (CURRENT_TIMESTAMP,(SELECT transactionid FROM 'transactions' WHERE status = '0'),?);""",[product[0]])

                db.commit()
                db.close()

                t = str(size) + " " + str(product[1]) + " x " + str(num) + "<br>"
                text += build_action_append("target", t)  
                text += build_action_refill("title", "Transaction in progress...")
                text += build_action_total(product[3])
                text += "</response>\n"
                self.send_header('Content-type', 'application/xml')  

            
            if action == 'cash':
                refund = 0                                                                              # Parameters
                typePayment = 0
                cash = 0
                for p in parts[1].split("&"):
                    sp = p.split("=")
                    if (sp[0] == 'refund'):
                        refund = sp[1]
                    if (sp[0] == 'type'):
                        typePayment = sp[1]    
                    if (sp[0] == 'cash'):
                        cash = sp[1]

                db = sqlite3.connect('products.db')
                cursor = db.cursor()
                cursor.execute("""SELECT productid FROM 'items' where transactionid=(SELECT transactionid FROM transactions WHERE status = '0');""")
                items = cursor.fetchall()                                                               # Fetches all items in the current transaction         
                items= [i[0] for i in items]
                print(items)

                # Try Deal 2 first
                product_class = []
                price =[]
                for i in items:                                                                         # For each item
                    cursor.execute("""SELECT classid FROM 'products' where productid=?;""",[i])         # Find classid
                    pr_class = cursor.fetchone()
                    product_class.append(pr_class)                                                      # Append to product_class list

                    cursor.execute("""SELECT price FROM 'products' where productid=?;""",[i])           # Find price
                    pr_price = cursor.fetchone()
                    price.append(pr_price)                                                              # Append to price list

                product_class = [p[0] for p in product_class]
                price = [p[0] for p in price]
                print(product_class)
                print(price)

                display =""
                count = numpy.unique(product_class, return_counts=True)                                 # Returns frequency of each product class
                count_t = numpy.unique(items, return_counts=True)                                       # Returns frequency of each product ID

                # Deal 2

                # Count no of 8s; pID 66,67,68: Valid Sides
                v = [i for i, e in enumerate(count_t[0]) if (e == 66 or e == 67 or e == 68)]
                sides_idx =  [i for i, e in enumerate(items) if (e == 66 or e == 67 or e == 68)]
                sides = count_t[1][v].sum()
                print('No of Cookie Sides: ', count_t[1][v].sum())
                print(sides_idx)
                display += 'No of Cookie Sides: ' + str(sides) + '<br>'

                # Count no of 1,2,3: Hot Drinks
                v = [i for i, e in enumerate(count[0]) if (e == 1 or e == 2 or e == 3)]
                drinks_idx = [i for i, e in enumerate(product_class) if (e == 1 or e == 2 or e == 3)]
                drinks = count[1][v].sum()
                print('No of Hot Drinks: ',count[1][v].sum())
                print(drinks_idx)
                display += 'No of Hot Drinks: ' + str(drinks) + '<br>'

                # Prep for Deal 1: Cold Drinks and other sides
                cold_drinks_idx = [i for i, e in enumerate(product_class) if e == 4]
                all_sides_idx = [i for i, e in enumerate(product_class) if e == 8]
                other_sides_idx = [i for i in all_sides_idx if (i not in sides_idx)]

                no_meal_deals = min(sides, drinks)
                print('No of MealDeal2 deals applicable: ',no_meal_deals)
                display += 'No of MealDeal2 deals applicable: ' + str(no_meal_deals) + '<br>'

                # Calculates discounted price and updates items table
                total_price = 0
                for i in range(0, no_meal_deals):
                    print('Deal: ', i+1)
                    display += 'Deal: ' + str(i+1) + '<br>'
                    org_price = round((price[drinks_idx[0]] + price[sides_idx[0]]),2)
                    dis_price = round((price[drinks_idx[0]] + price[sides_idx[0]]/2.0),2)
                    cursor.execute("""UPDATE items SET deal=2, discount=1 WHERE transactionid=(SELECT transactionid FROM transactions WHERE status = '0') AND productid=?;""",[items[sides_idx[0]]]) # side
                    cursor.execute("""UPDATE items SET deal=2, discount=0 WHERE transactionid=(SELECT transactionid FROM transactions WHERE status = '0') AND productid=?;""",[items[drinks_idx[0]]]) # drink

                    discount = round((org_price - dis_price),2)
                    print('Pay: ', dis_price, ' after discount of: ', discount)
                    display += 'Pay: ' + str(dis_price) + ' after discount of: ' + str(discount) + '<br>'
                    total_price += dis_price
                    drinks_idx.pop(0)
                    sides_idx.pop(0)

                print('Total from deals: ', total_price)  

                # Non MD#2 Items
                for i in cold_drinks_idx:
                    drinks_idx.append(i)
                for i in other_sides_idx:
                    sides_idx.append(i)
                    
                print('Items outside Meal Deal 2:')
                print('Drinks: ', drinks_idx)
                print('Sides: ', sides_idx)



                # Deal 1

                mains_idx = []

                if drinks_idx and sides_idx:

                    # Count no of 5,0,7: Sandwiches and Panninis
                    v = [i for i, e in enumerate(count[0]) if (e == 5 or e == 0 or e == 7)]
                    mains_idx = [i for i, e in enumerate(product_class) if (e == 5 or e == 0 or e == 7)]
                    mains = count[1][v].sum()
                    print('No of Mains: ',count[1][v].sum())
                    print(mains_idx)
                    display += 'No of Mains: ' + str(mains) + '<br>'
                    display += 'No of Drinks: ' + str(len(drinks_idx)) + '<br>'
                    display += 'No of Sides: ' + str(len(sides_idx)) + '<br>'

                    no_meal_deals = min(sides, mains, drinks)
                    print('No of MealDeal1 deals applicable: ',no_meal_deals)
                    display += 'No of MealDeal1 deals applicable: ' + str(no_meal_deals) + '<br>'

                    # Calculates discounted price and updates items table
                    for i in range(0, no_meal_deals):
                        print('Deal: ', i+1)
                        display += 'Deal: ' + str(i+1) + '<br>'
                        org_price = round((price[mains_idx[0]] + price[drinks_idx[0]] + price[sides_idx[0]]),2)
                        dis_price = round((price[mains_idx[0]] + price[drinks_idx[0]]),2)
                        cursor.execute("""UPDATE items SET deal=1, discount=2 WHERE transactionid=(SELECT transactionid FROM transactions WHERE status = '0') AND productid=?;""",[items[sides_idx[0]]]) # side
                        cursor.execute("""UPDATE items SET deal=1, discount=0 WHERE transactionid=(SELECT transactionid FROM transactions WHERE status = '0') AND productid=?;""",[items[drinks_idx[0]]]) # drink
                        cursor.execute("""UPDATE items SET deal=1, discount=0 WHERE transactionid=(SELECT transactionid FROM transactions WHERE status = '0') AND productid=?;""",[items[mains_idx[0]]]) # main

                        discount = round((org_price - dis_price),2)
                        print('Pay: ', dis_price, ' after discount of: ', discount)
                        display += 'Pay: ' + str(dis_price) + ' after discount of: ' + str(discount) + '<br>'
                        total_price += dis_price
                        mains_idx.pop(0)
                        drinks_idx.pop(0)
                        sides_idx.pop(0)

                    print('Total from deals: ', total_price)   
                    print('Items outside Meal deal 1:')
                    print('Mains: ', mains_idx)
                    print('Drinks: ', drinks_idx)
                    print('Sides: ', sides_idx)

                    
                    for i in mains_idx:
                        cursor.execute("""UPDATE items SET deal=0, discount=0 WHERE transactionid=(SELECT transactionid FROM transactions WHERE status = '0') AND productid=?;""",[items[i]]) 
                    
                    for i in drinks_idx:
                        cursor.execute("""UPDATE items SET deal=0, discount=0 WHERE transactionid=(SELECT transactionid FROM transactions WHERE status = '0') AND productid=?;""",[items[i]])

                    for i in sides_idx:
                        cursor.execute("""UPDATE items SET deal=0, discount=0 WHERE transactionid=(SELECT transactionid FROM transactions WHERE status = '0') AND (productid=?;""",[items[i]])           

                # Non MD#1 Items
                leftovers = []
                leftovers.append(mains_idx)
                leftovers.append(drinks_idx)
                leftovers.append(sides_idx)
                leftovers = list(chain(*leftovers))
                print('Non meal deal items:', leftovers)
                display += 'No. of non meal deal items:' + str(len(leftovers)) + '<br>'

                for i in leftovers:
                    total_price += price[i]

                total_price = round(total_price,2)    
                print('Total payment: ', total_price)

                print(total_price)    
                print(cash)
                change = (int(cash) - total_price)/100.0
                cursor.execute("""UPDATE transactions SET status=1, transactiontype=?, methodid=? WHERE transactionid=(SELECT transactionid FROM transactions WHERE status = '0');""", [refund, typePayment])
                cursor.execute("""INSERT into transactions (timestamp, status) VALUES (CURRENT_TIMESTAMP,0);""")
                db.commit()
                db.close()
                text = '<?xml version="1.0" encoding="UTF-8"?>\n'
                text += "<response>\n"
                text += build_action_total(total_price)
                text += build_action_refill("title", ('Transaction complete. Change: &pound;{}'.format(change)))
                text += build_action_append("target", display) 
                text += build_action_reset()
                text += "</response>\n"
                self.send_header('Content-type', 'application/xml') 
        
            if action == 'clr':
                db = sqlite3.connect('products.db')
                cursor = db.cursor()
                cursor.execute("""UPDATE transactions SET status=1, transactiontype=-1, methodid=-1 WHERE transactionid=(SELECT transactionid FROM transactions WHERE status = '0');""") # UPDATE query
                cursor.execute("""INSERT into transactions (timestamp, status) VALUES (CURRENT_TIMESTAMP,0);""")  # New Transaction
                
                db.commit()
                db.close()
                text = '<?xml version="1.0" encoding="UTF-8"?>\n'
                text += "<response>\n"
                text += build_action_total(200)
                text += build_action_refill("title",'Transaction voided.')
                text += build_action_reset()                                # Resets transactions
                text += "</response>\n"
                self.send_header('Content-type', 'application/xml') 

            if action == 'status':
                db = sqlite3.connect('products.db')
                cursor = db.cursor()
                cursor.execute("""SELECT productid FROM 'items' where transactionid=(SELECT transactionid FROM transactions WHERE status = '0');""")
                items = cursor.fetchall()                                   # Fetch all items in current transaction
                items= [i[0] for i in items]
                print(items)

                item_names = []
                for i in items:
                    cursor.execute("""SELECT name FROM 'products' where productid=?;""",[i])
                    name = cursor.fetchone()
                    item_names.append(name[0]) 

                text = '<?xml version="1.0" encoding="UTF-8"?>\n'
                text += "<response>\n"
                text += build_action_total(200)
                for n in item_names:
                    t = n + " x 1 <br>" 
                    text += build_action_append("target", t)                # Displays all items in current transaction when new window is loaded
                text += build_action_refill("title", "Transaction in progress...")
                text += build_action_total(200)  
                text += build_action_reset()
                text += "</response>\n"
                self.send_header('Content-type', 'application/xml')           

        else:
            self.send_response(404)
            fname = '404.html'
            file = open(fname, "r")
            text = file.read()
            self.send_header('Content-type', 'text/html')

        self.end_headers()
        self.wfile.write(text.encode("utf-8"))

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        self._set_headers()
        self.wfile.write("<html><body><h1>POST!</h1></body></html>")


def run(server_class=HTTPServer, handler_class=S, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd...')
    httpd.serve_forever()


if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()

    