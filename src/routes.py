from bson import ObjectId
from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.encoders import jsonable_encoder
from typing import List
import random
from pymongo.database import Database
import datetime
import pandas as pd

#Configure the router to export it to the main file
router = APIRouter()

#Read the data of the simulated database provided by Rocketfy
data = pd.read_csv('db_envios_challenge.csv')

#These arrays will be used afterwards to generate fake names for the Clients of the simulated database that don't contain a name already

maleFirstNames = ["Henry","Simeon","Payton","Cortez","Dwayne","Messiah","Austin","Raiden","Marvin","Emerson","Michael","Kamron","Frank","Ivan","Camden","Corbin","Roman","Skylar","Jase","Aron"]
femaleFirstNames = ["Livia","Brooklynn","Baylee","Khloe","Autumn","Thalia","Azul","Mylee","Nia","Emely","Justine","Itzel","Kyla","Aliza","Jaylyn","Laylah","Marisa","Donna","Sandra","Michaela"]
lastNames = ["Terrell","Melendez","Petersen","Ibarra","Silva","Reeves","Robinson","Choi","Larson","Kim","Hines","Shelton","Kennedy","Nguyen","Walker","Hampton","Lynch","Goodwin","Cole","Stevenson","Castro","Osborne","Underwood","Leach","Flynn","Sloan","Burch","Tran","Bowers","Chan"]

#These regular expressions will be used afterwards to help in the creation of the pipelines and filtering for the MongoDB queries

patternCompanyClients = r"(\w+)_(\d+)" #This pattern will be used to extract the strings with "text_Number" structure found inside "order_vendor_dbname" column, for example "bigcolors_1381618804" 
patternClients = r"^[a-zA-Z0-9]{24}$" #This pattern will be used to extract the strings with an alphanumerical structure found inside "order_vendor_dbname" column, for example "6465208fbc1391265257ed5d"
patternValidDates = r"^((?:19|20)\d\d)-((?:0[1-9]|1[0-2]))-(?:0[1-9]|[12][0-9]|3[01])$" #This pattern will be used to extract the dates with 'yyyy-mm-dd' structure found inside "shipping_date" column, for example "2023-06-01"

#This function generates simulated info of a "Client" for the registers that contain alphanumerical values inside the "order_vendor_dbname" column in the simulated data
def generateClientInfo(isMale : bool, identificationNumber : str):

    if(isMale):
        random_name = random.choice(maleFirstNames) 
    else:
        random_name = random.choice(femaleFirstNames)

    random_lastName = random.choice(lastNames)

    result = {"name" : " ".join([random_name, random_lastName]), 
              "email" : random_name+random_lastName+"_"+str(random.randint(1,100))+"@gmail.com", 
              "_id" : ObjectId(identificationNumber),
              "identificationNumber": identificationNumber} 
    
    return result

#This function generates the info of a "Company Client" for the registers that contain "text_Number" like values inside the "order_vendor_dbname" column in the simulated data
def generateCompanyClientInfo(companyClientName : str, identificationNumber : str):

    result = {"name" : companyClientName, 
              "email" : companyClientName+"_"+str(random.randint(1,100))+"@gmail.com", 
              "identificationNumber" : companyClientName +"_"+ identificationNumber} 
    
    return result
    


@router.get("/sendAlarm")
def sendAlarm(request: Request):

    #Access to database
    database: Database = request.app.database   
    alarmsCounter = 0

    pipelineAlarms = [
        {
            '$match': {
                'shipping_date' : {'$regex': patternValidDates},
                'shipping_status': {"$in": ["cancelled", "returned"]},
                '$or': [{'order_vendor_dbname': {'$regex': patternCompanyClients}}, {"order_vendor_dbname": {"$regex": patternClients}}]
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
                "from": 'Clients',
                "localField": "_id.order_vendor_dbname",
                "foreignField": "identificationNumber",
                "as": "client"
            }
        },
        {
            '$project':{
                '_id': 0,
                'clientName' : {'$arrayElemAt' : ['$client.name', 0]},
                'shipping_year': '$_id.shipping_year',
                'shippong_month': '$_id.shipping_month',
                'shipping_Id': '$shipping_ids',
                'clientEmail' : {'$arrayElemAt': ['$client.email', 0]}
            }
        } 
    ]

    for document in database["Orders"].aggregate(pipelineAlarms):
        print(document)
        alarmsCounter += 1
    
    print(alarmsCounter)

    return f"There is a total of {alarmsCounter} emails to be sent"

@router.get("/initData")
def initData(request: Request):

    clientsCounter = 0

    #Access to database
    database: Database = request.app.database
    database["Orders"].insert_many(data.to_dict('records'))

    # Build the aggregation pipelines
    pipelineCompanyClients = [
        {
            #Filter documents that follow the "companyClientName + _ + number" expression
            '$match': {
            'order_vendor_dbname': {'$regex': patternCompanyClients}
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
                        'regex': patternCompanyClients
                    }
                }
            }
        },
        { 
            #Decompose captured fields into their respective fields 
            '$project': {
                '_id': 0,
                'companyClientName':  {'$arrayElemAt' : ['$patternLike.captures', 0]},
                'companyIdentificationNumber': {'$arrayElemAt' : ['$patternLike.captures', 1]}
            }
        },
        
    ]

    pipelineClients = [
        {
            #Filter documents that have no special characters and are 24 characters long, in other words, ObjectsIds
            '$match': {
            'order_vendor_dbname': {'$regex': patternClients}
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
                'identificationNumber': '$_id'
            }
        }
    ]
    
    #Aggregate to the database
    print("printing results")
    clientsList = []

    #Generate Companies Info 
    for document in database["Orders"].aggregate(pipelineCompanyClients):
        client = generateCompanyClientInfo(document["companyClientName"], document["companyIdentificationNumber"])
        clientsCounter += 1
        clientsList.append(client)

    #Generate Natural Persons Info
    for document in database["Orders"].aggregate(pipelineClients):
        client = generateClientInfo(random.choice([True, False]), document["identificationNumber"])
        clientsCounter += 1
        clientsList.append(client)        

    print(clientsCounter)
    database['Clients'].insert_many(clientsList)
      
    return f"Sucessfully generated {clientsCounter} clientes"