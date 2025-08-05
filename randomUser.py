from random import choice, randrange
from string import ascii_uppercase, digits
import json, random

religions = ["hinduism", "christianity", "islam", "judaism", "atheism", "agnosticism", "Taoism", "Others"]

def createRandomUser():
    payload = {
    'age' : randrange(100),
    'sex' : ['M', 'F', 'O'][randrange(3)],
    'gender' : ['M', 'W', 'O'][randrange(3)],
    'religion' : getRandReligion(),
    'ethnicity' : ''.join(choice(ascii_uppercase) for i in range(10)),
    'pincode' : ''.join(choice(digits) for i in range(10)),
    'city' : ''.join(choice(ascii_uppercase) for i in range(10)),
    'district' :  ''.join(choice(ascii_uppercase) for i in range(10)),
    'state' :  ''.join(choice(ascii_uppercase) for i in range(10)),
    'country' :  ''.join(choice(ascii_uppercase) for i in range(10)),
    'nationality' :  ''.join(choice(ascii_uppercase) for i in range(10)),
    'public_key': ''.join(choice(ascii_uppercase) for i in range(10))
    }
    return payload


def getRandReligion():
    return religions[randrange(len(religions))]


def createRandomPost():
    with open('example.txt') as f:
        samples = json.loads(f.read())['samples']
    return random.choice(samples)
