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
