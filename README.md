# DSMarkets project

Το project αυτό αποτελεί την 2η εργασία στο πλαίσιο του μαθήματος Πληροφοριακών Συστημάτων. Αποτελεί ένα σύστημα ηλεκτρονικών αγορών με διάφορες δυνατότητες τόσο στον απλό χρήστη όσο και στον διαχειριστή. Το πρόγραμμα αυτό υλοποιήθηκε με python και το framework flask. Η βάση που χρησιμοποιήθηκε για την υλοποίηση ήταν η MongoDB, η οποία αποτελεί noSQL βάση. Τέλος, το web service μαζί με το image του Mongo τρέχουν με Docker και τα αποτελέσματα ελέγχθηκαν με το Postman.
## Περιγραφή εγκατάστασης του web service
Για το containirize της εφαρμογής δημιούργησα τα δύο αρχεία του docker, Dockerfile και docker-compose.yml.  
Το container της βάσης δεδομένων, έχει volume σε ένα φάκελο του host που θα ονομάζεται
data, ώστε στη περίπτωση που το container διαγραφεί, να αποφευχθεί η απώλεια των δεδομένων. Στην συνέχεια εκτελώ τις εντολές:

```bash
sudo apt-get install docker-compose
sudo docker-compose up -d
sudo docker ps
```
Δημιουργώ στην βάση δύο κενά collections users και products:
```bash
sudo docker cp users.json mongodb:/users.json
sudo docker cp products.json mongodb:/products.json
```
Γεμίζω τα κενά collections με τα αρχεία που έχω δημιουργήσει:
```bash
sudo docker exec -it mongodb mongoimport --db=DSMarkets --collection=Users --file=users.json
sudo docker exec -it mongodb mongoimport --db=DSMarkets --collection=Products --file=products.json
```
Για τερματισμό του container:
```bash
sudo docker-compose down
```
Για έναρξη του container για εκτέλεση της εφαρμογής: 
```bash
sudo docker-compose up -d
```


## Περιγραφή του κώδικα πριν την δημιουργία των @app.routes
Ξεκινώντας έκανα import τις απαραίτητες βιβλιοθήκες που χρειαζόμουν για την ανάπτυξη του κώδικα καθώς και κάποιες οι οποίες προέκυψαν κατά την ανάπτυξη του: 
```python
from pymongo import MongoClient
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError
from flask import Flask, request, jsonify, redirect, Response
import json, os, sys
import uuid
sys.path.append('./data')
import time
```
Στην συνέχεια δημιούργησα το path μεταξύ της MongoDB και του localhost προκειμένου η βάση να τρέχει τοπικά: 
```python
mongodb_hostname = os.environ.get("MONGO_HOSTNAME","localhost")
client = MongoClient('mongodb://'+mongodb_hostname+':27017/')
```
Ένα βήμα πριν την υλοποιήση των routes αρχικοποίησα την βάση, τα collections και το app του flask:
```python
db = client['DSMarkets']

products = db['Products']
users = db['Users']

app = Flask(__name__)
```


## User session and validation
Δημιουργία δύο συναρτήσεων που είναι απαραίτητες για την αυθεντικοποίηση του χρήστη κατά την σύνδεση του στο σύστημα που παράγει έναν μοναδικό 16ψήφιο μοναδικό αλφαριθμητικό:
```python
def create_session(username):
    user_uuid = str(uuid.uuid1())
    users_sessions[user_uuid] = (username, time.time())
    return user_uuid

def is_session_valid(user_uuid):
    return user_uuid in users_sessions
```

Λόγω του μεγάλου όγκου γραμμών που ακολοθούν στην πλειοψηφία των app.routes θα υπάρξει περιγραφή και μεμονωμένη επεξήγηση γραμμών.

## createUser
Για την δημιουργία του χρήστη ακολουθώ την φόρτωση των δεδομένων: 

```python
data = None
try:
   data = json.loads(request.data)
except Exception as e:
   return Response("bad json content",status=500,mimetype='application/json')
if data == None:
   return Response("bad request",status=500,mimetype='application/json')
if not "name" in data or not "password" in data:
   return Response("Information incomplete",status=500,mimetype="application/json")
```
Στην συνέχεια γεμίζω τα data που ο χρήστης δεν θα συμπληρώσει όπως το category και το orderHistory,
οι οποίες παίρνουν τις τιμές "user" (δημιουργία χρήστη σημαίνει πάντα απλός χρήστης) και κενή λίστα []
αντίστοιχα. Προχορώντας, αναζητώ εάν υπάρχει ίδιος χρήστης με το ίδιο mail και password. Αν υπάρχει τότε
εμφανίζω μήνυμα ότι ο χρήστης ήδη υπάρχει στην βάση, σε κάθε άλλη περίπτωση ο χρήστης με τα δεδομένα "name"
,"email" και "password" προστίθεται στην βάση εμφανίζοντας μήνυμα επιτυχημένης εγγραφής που φαίνεται και απο τον φάκελο create-user με τα συνοδευτικά screenshots για κάθε περίπτωση.

## login
Για το login φορτώνω επίσης τα δεδομένα που σημειώσα και παραπάνω. Έπειτα προσθέτω δύο global μεταβλητές οι οποίες φροντίζουν το καλάθι να μηδενίζει εάν γίνει ξαφνικό login από άλλον λογαριασμό:
```python
global_basket = []
total_cost = 0
email = "123@123.gr"
```
Έπειτα, ο χρήστης δίνοντας το έγκυρο email και τον κωδικό του μπαίνει στο σύστημα εμφανίζοντας μήνυμα επιτυχημένης σύνδεσης. Σε κάθε άλλη περίπτωση εμφανίζεται μήνυμα λάθους.

## search_product/id

Για το search_product/id φορτώνω επίσης τα δεδομένα που σημειώσα και παραπάνω με διαφορετικά τα δεδομένα που δίνονται στο πεδίο του μηνύματος "Information incomplete".
```python
if not "_id" in data:
```
Έπειτα αναζητώ ένα προιόν που με βάση του μοναδικού _id που δίνεται απο την Mongo και κάνοντας το απαραίτητο typecast αφού πρώτα έχω προσθέσει την βιβλιοθήκη:

```python
product = products.find_one({"_id":ObjectId(data['_id'])})
```

```python
from bson.objectid import ObjectId
```
Εάν το αναγνωριστικό που έχει δώσει ο χρήστης υπάρχει μέσα στην βάση τότε προσθέτω όλα τα δεδομένα του σε ένα dictionairy και τα εμφανίζω στον χρήστη. Σε κάθε άλλη περίπτωση εμφανίζεται μήνυμα λάθους. Σημειώνω επίσης πως ο χρήστης πρέπει να είναι αυθεντικοποιημένος: 
```python
    if (is_session_valid(uuid)):
```

## search_product/name

Για το search_product/name φορτώνω επίσης τα δεδομένα που σημειώσα και παραπάνω με διαφορετικά τα δεδομένα που δίνονται στο πεδίο του μηνύματος "Information incomplete".
```python
if not "name" in data:
```
Έπειτα αναζητώ τα προιόντα με το όνομα που έδωσε ο χρήστης με την μέθοδο find και τα προσθέτω στην λίστα iterable:

```python
iterable = products.find({"name": data['name']}
```
Στην περίπτωση που υπάρχουν προιόντα που έχω βρει με την find τότε δημιουργώ μια λίστα στην οποία προσθέτω όλα τα προιόντα που βρήκα με append τα οποία εμφανίζονται στο τέλος στον χρήστη
```python
products_list.append(item)
```
Όμως στον χρήστη πρέπει να εμφανίζονται ταξινομημένα με αλφαβητική σειρά (επέλεξα το category, αφού δεν μας προσδιορίζεται κάποια παράμετρος):
```python
return Response(json.dumps(sorted(products_list, key=lambda i: (i['category'])))
, status=200, mimetype='application/json')
```
Σημειώνω επίσης πως ο χρήστης πρέπει να είναι αυθεντικοποιημένος: 
```python
if (is_session_valid(uuid)):
```
## search_product/category
Για το search_product/category φορτώνω επίσης τα δεδομένα που σημειώσα και παραπάνω με διαφορετικά τα δεδομένα που δίνονται στο πεδίο του μηνύματος "Information incomplete".
```python
if not "category" in data:
```
Έπειτα αναζητώ τα προιόντα με το όνομα που έδωσε ο χρήστης με την μέθοδο find και τα προσθέτω στην λίστα iterable:

```python
iterable = products.find({"category": data['category']}
```
Στην περίπτωση που υπάρχουν προιόντα που έχω βρει με την find τότε δημιουργώ μια λίστα στην οποία προσθέτω όλα τα προιόντα που βρήκα με append τα οποία εμφανίζονται στο τέλος στον χρήστη
```python
products_list.append(item)
```
Όμως στον χρήστη πρέπει να εμφανίζονται ταξινομημένα με σειρά τιμής:
```python
return Response(json.dumps(sorted(products_list, key=lambda i: (i['price'])))
, status=200, mimetype='application/json')
```
Σημειώνω επίσης πως ο χρήστης πρέπει να είναι αυθεντικοποιημένος: 
```python
if (is_session_valid(uuid)):
```
## add_shopping_basket
Για την μέθοδο αυτή ο χρήστης πρέπει να συμπληρώσει το email, το _id του προιόντος που θέλει να αγοράσει καθώς και την ποσότητα stock. Τα δεδομένα φορτώνονται με τον ίδιο τρόπο που υπάρχει και στα παραπάνω app.routes με την μόνη διαφορά:
```python
if not "email" in data or not "_id" in data or not "stock" in data:
```
Στην συνέχεια για να υλοποιηθεί αυτή η μέθοδος απαιτείται είσοδος με λογαριασμό "user" για αυτό και το ελέγχω:
```python
if (user['category'] == 'user'):
```
Εάν δεν είναι "user" ο χρήστης που προσπαθεί να αγοράσει απόθεμα τότε εμφανίζεται κατάλληλο μήνυμα. Έπειτα αναζητώ ένα προιόν που με βάση του μοναδικού _id που δίνεται απο την Mongo και κάνοντας το απαραίτητο typecast: 
```python
product = products.find_one({"_id": ObjectId(data['_id'])})
```
Πρέπει επίσης να ελέγξω εάν η ποσότητα που επιθυμεί ο χρήστης να αγοράσει διατίθεται στο κατάστημα. Υπάρχει πιθανότητα να μην διατείθεται για τον λόγο αυτόν κάνω τις απαραίτητες ενέργειες: 
```python
            if product is not None:
                if data['stock'] > product['stock']:
                    return Response("Quantity unavailable", status=400, mimetype='application/json')
```
Αν όμως η ποσότητα που ζητάει υπάρχει και μπορεί να αγοραστεί τότε προχωράμε στην αγόρα. Στο συνολικό κόστος προστίθεται ο αριθμός που προκύπτει απο το γινόμενο της ποσότητας και της τιμής. Ταυτόχρονα, πρέπει να αφαιρεθεί και η ποσότητα του προιόντος που δεσμεύτηκε απο τον πελάτη. Τέλος δημιουργώ ένα dictionairy item στο οποίο προσθέτω τα στοιχεία της παραγγελίας για το προιόν:
```python
global total_cost
total_cost += data['stock']*product['price']
products.update({"_id": ObjectId(data['_id'])}, {"$set": {"stock": product['stock']-data['stock']}})
item = {'name':product["name"], 'price':product["price"],'stock':data["stock"]}
global_basket.append(item)
msg = "Your shopping cart until now"+str(global_basket)+"and the total cost is: "+str(total_cost)
```
## check_shopping_basket
Για την μέθοδο αυτή ο χρήστης πρέπει να συμπληρώσει το email. Τα δεδομένα φορτώνονται με τον ίδιο τρόπο που υπάρχει και στα παραπάνω app.routes με την μόνη διαφορά:
```python
if not "email" in data:
```
Το καλάθι που ανήκει σε αυτό το email έχει ήδη γεμίσει (εάν έχει περάσει βέβαια απο το add_shopping_basket route) το οποίο είναι global μεταβλητή. Οπότε:
```python
msg = "Your shopping cart until now" + str(global_basket) + "and the total cost is: " + str(total_cost)
return Response(msg, status=200, mimetype='application/json')
```
Επίσης για να υλοποιηθεί αυτή η μέθοδος απαιτείται είσοδος με λογαριασμό "user" για αυτό και το ελέγχω:
```python
if (user['category'] == 'user'):
```
## delete_product_basket
Για την μέθοδο αυτή ο χρήστης πρέπει να συμπληρώσει το email, το _id του προιόντος που θέλει να διαγράψει. Τα δεδομένα φορτώνονται με τον ίδιο τρόπο που υπάρχει και στα παραπάνω app.routes με την μόνη διαφορά:
```python
if not "email" in data or not "_id" in data:
```
Στην συνέχεια για να υλοποιηθεί αυτή η μέθοδος απαιτείται είσοδος με λογαριασμό "user" για αυτό και το ελέγχω:
```python
if (user['category'] == 'user'):
```
Εάν δεν είναι "user" ο χρήστης που προσπαθεί να διαγράψει τότε εμφανίζεται κατάλληλο μήνυμα. Έπειτα αναζητώ ένα προιόν που με βάση του μοναδικού _id που δίνεται απο την Mongo και κάνοντας το απαραίτητο typecast: 
```python
product = products.find_one({"_id": ObjectId(data['_id'])})
```
Στην συνέχεια προσπαθώ να βρώ εάν υπάρχει στο καλάθι προιόν που το όνομα του συμπίπτει με το _id του product που εντόπισα στην βάση. Έαν υπάρχει τότε αφαιρώ το γινόμενο του διαγραμένου προιόντος με την ποσότητα και την τιμή του και επιστρέφω στην βάση των προιόντων το stock στο επίπεδο που ήταν επιστρέφοντας το δεσμευμένο απόθεμα:
```python
global total_cost
for i in range(len(global_basket)):
  if global_basket[i]['name'] == product["name"]:
     total_cost -= global_basket[i]['stock'] * product['price']
     products.update({"_id": ObjectId(data['_id'])},{"$set": {"stock": product['stock'] + global_basket[i]['stock']}})
     del global_basket[i]
     break
msg = "Your shopping cart until now" + str(global_basket) + "and the total cost is: " + str(total_cost)
```
## buy_all_products
Για την μέθοδο αυτή ο χρήστης πρέπει να συμπληρώσει το email και την card που αποτελεί τον αριθμό της κάρτας που θέλει να εισάγει:
```python
if not "email" in data or not "card" in data:
```
Στην συνέχεια για να υλοποιηθεί αυτή η μέθοδος απαιτείται είσοδος με λογαριασμό "user" για αυτό και το ελέγχω:
```python
if (user['category'] == 'user'):
```
Για να αγοραστεί το καλάθι πρέπει ο χρήστης να συμπληρώσει τον 16ψήφιο αριθμό της κάρτας του. Για αυτό τον λόγο γίνεται και ο έλεγχος για το μήκος της κάρτας. Αν αγοραστεί τότε το καλάθι αδειάζει και τα προιόντα στην βάση τηρούν το νέο τους απόθεμα. Τέλος ενημερώνεται και το πεδίο orderHistory του χρήστη με το καλάθι που μόλις αγοράστηκε και εμφανίζεται στον χρήστη η απόδειξη αγοράς:
```python
 if(len(data["card"])!=16):
    return Response("Card number must contain 16 digits", status=400, mimetype='application/json')
order_history = user["orderHistory"]
order_history.append(global_basket)
users.update_one({'email': data["email"]}, {"$set": {"orderHistory": order_history}})
msg = "Receipt" + str(global_basket) + "and the total cost is: " + str(total_cost)
return Response(msg, status=200, mimetype='application/json')
```
## get_order_history
Για την μέθοδο αυτή ο χρήστης πρέπει να συμπληρώσει το email. Τα δεδομένα φορτώνονται με τον ίδιο τρόπο που υπάρχει και στα παραπάνω app.routes με την μόνη διαφορά:
```python
if not "email" in data:
```
Στην συνέχεια για να υλοποιηθεί αυτή η μέθοδος απαιτείται είσοδος με λογαριασμό "user" για αυτό και το ελέγχω:
```python
if (user['category'] == 'user'):
```
Αναζητώ τον χρήστη και στην συνέχεια αφού τον έχω βρεί ελέγχω το πεδίο του orderHistory:
```python
user = {'orderHistory':user["orderHistory"]}
return Response(json.dumps(user), status=200, mimetype='application/json')
```

## delete_user 
Για να μπορεί ο συνδεδεμένος χρήστης στο σύστημα να διαγράψει τον λογαριασμό του και μόνο πρέπει να κρατάω το δεδομένο του email του. Αυτό το κάνω στο σημείο του login. Συνεπώς συγκρίνω το email που δίνει με αυτό που έχω κρατήσει στην σύνδεση του. Εάν αυτό είναι ίδιο τότε τον διαγράφω απο την βάση:
```python
global email

if is_session_valid(uuid):
   user = users.find_one({"email": data['email']})
   if user['category'] == 'user' and email == data['email']:
      msg = (user['name']+" was deleted.")
      users.delete_one({"email":data['email']})
      return Response(msg, status=200, mimetype='application/json')
   else:
      return Response("You can only delete your user account", status=400, mimetype='application/json')
```
## add_product as an admin
Για την μέθοδο αυτή ο χρήστης πρέπει να συμπληρώσει το email, το price του προιόντος που θέλει να προσθέσει, την ποσότητα stock καθώς και το category και description. Τα δεδομένα φορτώνονται με τον ίδιο τρόπο που υπάρχει και στα παραπάνω app.routes με την μόνη διαφορά:
```python
if not "email" in data or not "price" in data or not "stock" in data or not "category" in data or not "description" in data:
```
Στην συνέχεια για να υλοποιηθεί αυτή η μέθοδος απαιτείται είσοδος με λογαριασμό "admin" για αυτό και το ελέγχω:
```python
if (user['category'] == 'admin'):
```
Δημιουργώ ένα dictionairy product το οποίο το γεμίζω με τα δεδομένα που εισάγει ο χρήστης και στην συνέχεια το προσθέτω στην βάση:
```python
product = {
                "name": data['name'],
                "price": data['price'],
                "description": data['description'],
                "category": data['category'],
                "stock": data['stock']
            }
products.insert_one(product)
return Response("Product was added succesfully", status=200, mimetype='application/json')
```

## delete_product as an admin
Για την μέθοδο αυτή ο χρήστης πρέπει να συμπληρώσει το email, το _id του προιόντος που θέλει να διαγράψει. Τα δεδομένα φορτώνονται με τον ίδιο τρόπο που υπάρχει και στα παραπάνω app.routes με την μόνη διαφορά:
```python
if not "email" in data or not "_id" in data:
```
Στην συνέχεια για να υλοποιηθεί αυτή η μέθοδος απαιτείται είσοδος με λογαριασμό "admin" για αυτό και το ελέγχω:
```python
if (user['category'] == 'admin'):
```
Εάν δεν είναι "admin" ο χρήστης που προσπαθεί να διαγράψει τότε εμφανίζεται κατάλληλο μήνυμα. Έπειτα αναζητώ ένα προιόν που με βάση του μοναδικού _id που δίνεται απο την Mongo και κάνοντας το απαραίτητο typecast. Τέλος διαγράφω το προιόν απο την βάση:
```python
product = products.delete_one({"_id": ObjectId(data['_id'])})
```

## update_product as an admin
Για την μέθοδο αυτή ο χρήστης πρέπει να συμπληρώσει το email, το price του προιόντος που θέλει να προσθέσει, την ποσότητα stock καθώς και το category και description. Τα δεδομένα φορτώνονται με τον ίδιο τρόπο που υπάρχει και στα παραπάνω app.routes με την μόνη διαφορά:
```python
if not "email" in data or not "price" in data or not "stock" in data or not "category" in data or not "description" in data:
```
Στην συνέχεια για να υλοποιηθεί αυτή η μέθοδος απαιτείται είσοδος με λογαριασμό "admin" για αυτό και το ελέγχω:
```python
if (user['category'] == 'admin'):
```
Ελέγχω εάν τα δεδομένα που έχει δώσει προς αλλαγή περιέχουν κάποια τιμή. Αν έχει τότε αλλάζω το συγκεκριμένο πεδίο αλλιώς παραμένει ίδιο:
```python
if data["name"] is not None:
      products.update({"_id": ObjectId(data['_id'])}, {"$set": {"name": data['name']}})
if data["price"] is not None:
      products.update({"_id": ObjectId(data['_id'])}, {"$set": {"price": data['price']}})
if data["description"] is not None:
     products.update({"_id": ObjectId(data['_id'])}, {"$set": {"description": data['description']}})
if data["stock"] is not None:
     products.update({"_id": ObjectId(data['_id'])}, {"$set": {"stock": data['stock']}})
return Response("Product was updated succesfully", status=200, mimetype='application/json')
```

## Επίλογος 
Σε κάθε συνάρτηση και κάθε περίπτωση υπάρχουν μηνύματα λάθος με τα απαραίτητα status codes. Δεν ανέφερα περισσότερες λεπτομέρειες για αυτά αφού στην πλειοψηφία των περιπτώσεων είναι επαναλαμβανόμενες.
