from bson import ObjectId
from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.encoders import jsonable_encoder
from typing import List
import random
from pymongo.database import Database
import datetime
import pandas as pd

router = APIRouter()

data = pd.read_csv('db_envios_challenge.csv')

maleFirstNames = ["Henry","Simeon","Payton","Cortez","Dwayne","Messiah","Austin","Raiden","Marvin","Emerson","Michael","Kamron","Frank","Ivan","Camden","Corbin","Roman","Skylar","Jase","Aron"]
femaleFirstNames = ["Livia","Brooklynn","Baylee","Khloe","Autumn","Thalia","Azul","Mylee","Nia","Emely","Justine","Itzel","Kyla","Aliza","Jaylyn","Laylah","Marisa","Donna","Sandra","Michaela"]
lastNames = ["Terrell","Melendez","Petersen","Ibarra","Silva","Reeves","Robinson","Choi","Larson","Kim","Hines","Shelton","Kennedy","Nguyen","Walker","Hampton","Lynch","Goodwin","Cole","Stevenson","Castro","Osborne","Underwood","Leach","Flynn","Sloan","Burch","Tran","Bowers","Chan"]

#Create the regex expressions to be used inside the pipelines
patternCompanies = r"(\w+)_(\d+)"
patternNaturalPersons = r"^[a-zA-Z0-9]{24}$"
patternValidDates = r"^((?:19|20)\d\d)-((?:0[1-9]|1[0-2]))-(?:0[1-9]|[12][0-9]|3[01])$"

def generateUserInfo(isMale : bool, identificationNumber : str):

    if(isMale):
        random_name = random.choice(maleFirstNames)
        random_lastName = random.choice(lastNames)
    else:
        random_name = random.choice(femaleFirstNames)
        random_lastName = random.choice(lastNames)

    finalIdentificationNumber = None

    if(identificationNumber != 0):
        finalIdentificationNumber = identificationNumber

    result = {"name" : " ".join([random_name, random_lastName]), 
              "email" : random_name+random_lastName+"_"+str(random.randint(1,100))+"@gmail.com", 
              "_id" : ObjectId(identificationNumber),
              "identificationNumber": identificationNumber} 
    
    return result

def generateCompanyInfo(companyName : str, identificationNumber : str):

    result = {"name" : companyName, 
              "email" : companyName+"_"+str(random.randint(1,100))+"@gmail.com", 
              "identificationNumber" : companyName +"_"+ identificationNumber} 
    
    return result
    


@router.get("/SendAlarm")
def sendAlarm(request: Request):

    #Access to database
    database: Database = request.app.database   
    counterAlarms = 0

    pipelineAlarms = [
        {
            '$match': {
                'shipping_date' : {'$regex': patternValidDates},
                'shipping_status': {"$in": ["cancelled", "returned"]},
                '$or': [{'order_vendor_dbname': {'$regex': patternCompanies}}, {"order_vendor_dbname": {"$regex": patternNaturalPersons}}]
            }
        },
        {
            '$addFields':{
                'regexResult': {'$regexFind': {
                        'input': '$shipping_date',
                        'regex': patternValidDates
                    }
                }
            }
        },
        {
            '$project':{
                '_id': 0,
                'shipping_id': '$shipping_id',
                'shipping_year': {'$arrayElemAt' : ['$regexResult.captures', 0] },
                'shipping_month': {'$arrayElemAt' : ['$regexResult.captures', 1] },
                'order_vendor_dbname': '$order_vendor_dbname'
            }
        },
        {
            '$group':{
                '_id': {
                    'order_vendor_dbname': '$order_vendor_dbname',
                    'shipping_year': '$shipping_year',
                    'shipping_month': '$shipping_month'
                },
                'shipping_ids': { '$push': '$shipping_id'},
                'count': {'$sum': 1}
            }
        },
        {
             '$match': {
                "count": { "$gte": 3 }
            }
        },
        {
            '$lookup': {
                "from": 'Users',
                "localField": "_id.order_vendor_dbname",
                "foreignField": "identificationNumber",
                "as": "user"
            }
        },
        {
            '$project':{
                '_id': 0,
                'userName' : {'$arrayElemAt' : ['$user.name', 0]},
                'shipping_year': '$_id.shipping_year',
                'shippong_month': '$_id.shipping_month',
                'shipping_Id': '$shipping_ids',
                'userEmail' : {'$arrayElemAt': ['$user.email', 0]}
            }
        } 
    ]

    for document in database["Orders"].aggregate(pipelineAlarms):
        print(document)
        counterAlarms += 1
    
    print(counterAlarms)

    return f"There is a total of {counterAlarms} emails to be sent"

@router.get("/initData")
def initData(request: Request):

    counterDocuments = 0
    # usersList = generateUsers(50)

    #Access to database
    database: Database = request.app.database
    # database["Orders"].insert_many(data.to_dict('records'))

    # Build the aggregation pipelines
    pipelineCompanies = [
        {
            #Filter documents that follow the "companyName + _ + number" expression
            '$match': {
            'order_vendor_dbname': {'$regex': patternCompanies}
            }
        },
        {
            #Group the query by the column "order_vendor_dbname" previously filtered
            '$group': {
            '_id': '$order_vendor_dbname',
            'count': {'$sum': 1}
        }
        },
        { 
            #Save all data returned by regexFind in the field patternLike
            '$project': {
                '_id': 0,
                'patternLike': {
                    '$regexFind': {
                        'input': '$_id',
                        'regex': patternCompanies
                    }
                }
            }
        },
        { 
            #Decompose captured fields into their respective fields 
            '$project': {
                '_id': 0,
                'companyName':  {'$arrayElemAt' : ['$patternLike.captures', 0]},
                'companyNumber': {'$arrayElemAt' : ['$patternLike.captures', 1]}
            }
        },
        
    ]

    pipelineNaturalPersons = [
        {
            #Filter documents that have no special characters and are 24 characters long, in other words, ObjectsIds
            '$match': {
            'order_vendor_dbname': {'$regex': patternNaturalPersons}
            }
        },
        {
            #Group the query by the column "order_vendor_dbname" previously filtered
            '$group':{
                '_id': '$order_vendor_dbname',
                'count': {'$sum': 1}
            }
        },
        {
            #Save the objectId element
            '$project':{
                '_id':0,
                'identificationCode': '$_id'
            }
        }
    ]
    
    #Aggregate to the database
    print("printing results")
    usersList = []

    #Generate Companies Info 
    for document in database["Orders"].aggregate(pipelineCompanies):
        user = generateCompanyInfo(document["companyName"], document["companyNumber"])
        usersList.append(user)

    #Generate Natural Persons Info
    for document in database["Orders"].aggregate(pipelineNaturalPersons):
        user = generateUserInfo(random.choice([True, False]), document["identificationCode"])
        usersList.append(user)        

    print(counterDocuments)
    database['Users'].insert_many(usersList)
      
    return f"Sucessfully generated {counterDocuments}"