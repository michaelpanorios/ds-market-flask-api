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
