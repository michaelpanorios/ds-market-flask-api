from pymongo import MongoClient
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError
from flask import Flask, request, jsonify, redirect, Response
import json, os, sys
import uuid
sys.path.append('./data')
import time

# Connect to our local MongoDB
mongodb_hostname = os.environ.get("MONGO_HOSTNAME","localhost")
client = MongoClient('mongodb://'+mongodb_hostname+':27017/')

# Choose database
db = client['DSMarkets']

# Choose collections
products = db['Products']
users = db['Users']

# Initiate Flask App
app = Flask(__name__)

users_sessions = {}

def create_session(username):
    user_uuid = str(uuid.uuid1())
    users_sessions[user_uuid] = (username, time.time())
    return user_uuid

def is_session_valid(user_uuid):
    return user_uuid in users_sessions

# Creating a user
@app.route('/createUser', methods=['POST'])
def create_user():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "name" in data or not "password" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")

    data['category']="user"
    data['orderHistory']=[]

    if users.find({"email":data['email']}).count() == 0 :
        user =  {
                    "name": data['name'],
                    "email": data['email'],
                    "password": data['password'],
                    "category": data['category'],
                    "orderHistory": data['orderHistory']
                }
        users.insert_one(user)
        return Response(data['name']+" was added to the MongoDB", status=200, mimetype='application/json')
    else:
        return Response("A user with the given username already exists", status=400, mimetype='application/json')


global_basket = []
total_cost = 0
email = "123@123.gr"
# Login into the system
@app.route('/login', methods=['POST'])
def login():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "email" in data or not "password" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")

    user = users.find_one({"email":data['email']},{"password":data['password']})

    global global_basket
    global total_cost
    global email
    global_basket = []
    total_cost = 0
    email = data['email']

    if user!=None:
        user_uuid = create_session(data['email'])
        res = {"uuid": user_uuid, "email": data['email']}
        return Response(json.dumps(res), status=200, mimetype='application/json')
    else:
        return Response("Wrong username or password, please re-enter valid data", status=400, mimetype='application/json')

# Search products based on id
@app.route('/search_product/id', methods=['GET'])
def search_products_id():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
        uuid = request.headers.get('authorization')
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data == None:
        return Response("bad request", status=500, mimetype='application/json')
    if not "_id" in data:
        return Response("Information incomplete", status=500, mimetype="application/json")

    if (is_session_valid(uuid)):
        product = products.find_one({"_id":ObjectId(data['_id'])})
        if (product != None):
            product = {'name': product["name"], 'description': product["description"],
                       'price': product["price"], 'category': product["category"], 'stock':product["stock"]}
            return Response(json.dumps(product), status=200, mimetype='application/json')
        else:
            return Response("Product not found", status=400, mimetype='application/json')
    else:
        return Response("Non authenticated user", status=401, mimetype='application/json')

# Search products based on name
@app.route('/search_product/name', methods=['GET'])
def search_products_name():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
        uuid = request.headers.get('authorization')
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data == None:
        return Response("bad request", status=500, mimetype='application/json')
    if not "name" in data:
        return Response("Information incomplete", status=500, mimetype="application/json")

    if (is_session_valid(uuid)):
        iterable = products.find({"name": data['name']})
        products_list = []
        for product in iterable:
            item = {'name': product["name"], 'description': product["description"],
                       'price': product["price"], 'category': product["category"], 'stock':product["stock"]}
            products_list.append(item)
        # Alphabetical order
        if not products_list:
            return Response("Products not found", status=400, mimetype='application/json')
        return Response(json.dumps(sorted(products_list, key=lambda i: (i['category']))), status=200, mimetype='application/json')
    else:
        return Response("Non authenticated user", status=401, mimetype='application/json')

# Search products based on category
@app.route('/search_product/category', methods=['GET'])
def search_products_category():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
        uuid = request.headers.get('authorization')
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data == None:
        return Response("bad request", status=500, mimetype='application/json')
    if not "category" in data:
        return Response("Information incomplete", status=500, mimetype="application/json")

    uuid = request.headers.get('authorization')
    if (is_session_valid(uuid)):
        iterable = products.find({"category": data['category']})
        products_list = []
        for product in iterable:
            item = {'name': product["name"], 'description': product["description"],'price': product["price"], 'category': product["category"], 'stock':product["stock"]}
            products_list.append(item)
        if not products_list:
            return Response("Products not found", status=400, mimetype='application/json')
        return Response(json.dumps(sorted(products_list, key=lambda i: (i['price']))), status=200, mimetype='application/json')
    else:
        return Response("Non authenticated user", status=401, mimetype='application/json')


# Adding products to shopping basket
@app.route('/add_shopping_basket', methods=['PATCH'])
def shopping_basket():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
        uuid = request.headers.get('authorization')
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data == None:
        return Response("bad request", status=500, mimetype='application/json')
    if not "email" in data or not "_id" in data or not "stock" in data:
        return Response("Information incomplete", status=500, mimetype="application/json")

    if (is_session_valid(uuid)):
        user = users.find_one({"email": data['email']})
        if (user['category'] == 'user'):
            product = products.find_one({"_id": ObjectId(data['_id'])})
            if product is not None:
                if data['stock'] > product['stock']:
                    return Response("Quantity unavailable", status=400, mimetype='application/json')
                global total_cost
                total_cost += data['stock']*product['price']
                products.update({"_id": ObjectId(data['_id'])}, {"$set": {"stock": product['stock']-data['stock']}})
                item = {'name':product["name"], 'price':product["price"],'stock':data["stock"]}
                global_basket.append(item)
                msg = "Your shopping cart until now"+str(global_basket)+"and the total cost is: "+str(total_cost)
                return Response(msg, status=200, mimetype='application/json')
            else:
                return Response("Product not found", status=400, mimetype='application/json')
        else:
            return Response("Permission only to Users", status=400, mimetype='application/json')
    else:
        return Response("Non authenticated user", status=401, mimetype='application/json')

# Showing the shopping basket of a user
@app.route('/check_shopping_basket', methods=['GET'])
def returning_basket():
# Request JSON data
    data = None
    try:
        data = json.loads(request.data)
        uuid = request.headers.get('authorization')
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "email" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")

    if (is_session_valid(uuid)):
        user = users.find_one({"email": data['email']})
        if (user['category'] == 'user'):
            msg = "Your shopping cart until now" + str(global_basket) + "and the total cost is: " + str(total_cost)
            return Response(msg, status=200, mimetype='application/json')
        else:
            return Response("Permission only to Users", status=400, mimetype='application/json')
    else:
        return Response("Non authenticated user", status=401, mimetype='application/json')


# Deleting a product from basket
@app.route('/delete_product_basket', methods=['DELETE'])
def deleting_product_basket():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
        uuid = request.headers.get('authorization')
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data == None:
        return Response("bad request", status=500, mimetype='application/json')
    if not "email" in data or not "_id" in data:
        return Response("Information incomplete", status=500, mimetype="application/json")

    if (is_session_valid(uuid)):
        user = users.find_one({"email": data['email']})
        if (user['category'] == 'user'):
            product = products.find_one({"_id": ObjectId(data['_id'])})
            if product is not None:
                global total_cost
                for i in range(len(global_basket)):
                    if global_basket[i]['name'] == product["name"]:
                        total_cost -= global_basket[i]['stock'] * product['price']
                        products.update({"_id": ObjectId(data['_id'])},{"$set": {"stock": product['stock'] + global_basket[i]['stock']}})
                        del global_basket[i]
                        break
                msg = "Your shopping cart until now" + str(global_basket) + "and the total cost is: " + str(total_cost)
                return Response(msg, status=200, mimetype='application/json')
            else:
                return Response("Product doesn't exist in your cart", status=400, mimetype='application/json')
        else:
            return Response("Permission only to Users", status=400, mimetype='application/json')
    else:
        return Response("Non authenticated user", status=401, mimetype='application/json')


# Buy all products from basket
@app.route('/buy_all_products', methods=['PATCH'])
def buy_products():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
        uuid = request.headers.get('authorization')
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data == None:
        return Response("bad request", status=500, mimetype='application/json')
    if not "email" in data or not "card" in data:
        return Response("Information incomplete", status=500, mimetype="application/json")

    if (is_session_valid(uuid)):
        user = users.find_one({"email": data['email']})
        if (user['category'] == 'user'):
            if(len(data["card"])!=16):
                return Response("Card number must contain 16 digits", status=400, mimetype='application/json')
            order_history = user["orderHistory"]
            order_history.append(global_basket)
            users.update_one({'email': data["email"]}, {"$set": {"orderHistory": order_history}})
            msg = "Receipt" + str(global_basket) + "and the total cost is: " + str(total_cost)
            return Response(msg, status=200, mimetype='application/json')
        else:
            return Response("Permission only to Users", status=400, mimetype='application/json')
    else:
        return Response("Non authenticated user", status=401, mimetype='application/json')


# Buy all products from basket
@app.route('/get_order_history', methods=['GET'])
def get_products():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
        uuid = request.headers.get('authorization')
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data == None:
        return Response("bad request", status=500, mimetype='application/json')
    if not "email" in data:
        return Response("Information incomplete", status=500, mimetype="application/json")

    if (is_session_valid(uuid)):
        user = users.find_one({"email": data['email']})
        if (user['category'] == 'user'):
            user = {'orderHistory':user["orderHistory"]}
            return Response(json.dumps(user), status=200, mimetype='application/json')
        else:
            return Response("User not found", status=400, mimetype='application/json')
    else: 
        return Response("Non authenticated user", status=401, mimetype='application/json')

# Delete user from database
@app.route('/delete_user', methods=['DELETE'])
def delete_user():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
        uuid = request.headers.get('authorization')
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "email" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")

    global email

    if is_session_valid(uuid):
        user = users.find_one({"email": data['email']})
        if user['category'] == 'user' and email == data['email']:
            msg = (user['name']+" was deleted.")
            users.delete_one({"email":data['email']})
            return Response(msg, status=200, mimetype='application/json')
        else:
            return Response("You can only delete your user account", status=400, mimetype='application/json')
    else:
        return Response("Non authenticated user", status=401, mimetype='application/json')


# ---------------------------------------------------------------------------------------------------------------------------------------------------------

# Adding a product to products list as an admin
@app.route('/add_product', methods=['POST'])
def add_product_admin():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
        uuid = request.headers.get('authorization')
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data == None:
        return Response("bad request", status=500, mimetype='application/json')
    if not "name" in data or not "price" in data or not "description" in data or not "category" in data or not "stock" in data or not "email" in data:
        return Response("Information incomplete", status=500, mimetype="application/json")

    if (is_session_valid(uuid)):
        user = users.find_one({"email":data['email']})
        if (user['category']=="admin"):
            product = {
                "name": data['name'],
                "price": data['price'],
                "description": data['description'],
                "category": data['category'],
                "stock": data['stock']
            }
            products.insert_one(product)
            return Response("Product was added succesfully", status=200, mimetype='application/json')
        else:
            return Response("Account has no permission. Must be an admin", status=400, mimetype='application/json')
    else:
        return Response("Non authenticated user", status=401, mimetype='application/json')

# Delete a product from products as an admin
@app.route('/delete_product', methods=['DELETE'])
def delete_product_admin():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
        uuid = request.headers.get('authorization')
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "_id" in data or not "email" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")

    # Maybe I need to find the product with its _id before deleting it
    if (is_session_valid(uuid)):
        user = users.find_one({"email": data['email']})
        if (user['category'] == 'admin'):
            products.delete_one({"_id":ObjectId(data['_id'])})
            return Response("Product was deleted succesfully", status=200, mimetype='application/json')
        else:
            return Response("Account has no permission. Must be an admin", status=400, mimetype='application/json')
    else:
        return Response("Non authenticated user", status=401, mimetype='application/json')

# Update product details as an admin
@app.route('/update_product', methods=['PATCH'])
def update_product_admin():
    # Request JSON data
    data = None

    try:
        data = json.loads(request.data)
        uuid = request.headers.get('authorization')
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data == None:
        return Response("bad request", status=500, mimetype='application/json')
    if not "email" in data:
        return Response("Information incomplete", status=500, mimetype="application/json")

    # Maybe I need to find the product with its _id before updating it
    if (is_session_valid(uuid)):
        user = users.find_one({"email": data['email']})
        if (user['category'] == 'admin'):
            if data["name"] is not None:
                products.update({"_id": ObjectId(data['_id'])}, {"$set": {"name": data['name']}})
            if data["price"] is not None:
                products.update({"_id": ObjectId(data['_id'])}, {"$set": {"price": data['price']}})
            if data["description"] is not None:
                products.update({"_id": ObjectId(data['_id'])}, {"$set": {"description": data['description']}})
            if data["stock"] is not None:
                products.update({"_id": ObjectId(data['_id'])}, {"$set": {"stock": data['stock']}})
            return Response("Product was updated succesfully", status=200, mimetype='application/json')
        else:
            return Response("Account has no permission. Must be an admin", status=400, mimetype='application/json')
    else:
        return Response("Non authenticated user", status=401, mimetype='application/json')





# Εκτέλεση flask service σε debug mode, στην port 5000.
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
