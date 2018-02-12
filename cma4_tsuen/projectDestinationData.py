import urllib.request
import json
import dml
import prov.model
import datetime
import uuid

class projectDestinationData(dml.Algorithm):
    contributor = 'cma4_tsuen'
    reads = ['cma4_tsuen.entertainment', 'cma4_tsuen.food']
    writes = ['cma4_tsuen.destinationsProjected']

    @staticmethod
    def execute(trial = False):
        '''Retrieve some data sets (not using the API here for the sake of simplicity).'''
        startTime = datetime.datetime.now()

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('cma4_tsuen', 'cma4_tsuen')

        dataSet = []

        collection = repo['cma4_tsuen.entertainment'].find()

        # projection
        dataSet = [
        	{'name': row["BUSINESSNAME"],
        	'Coords': row["Location"]}
        	for row in collection
        ]

        collection2 = repo['cma4_tsuen.food'].find()

        food_data = []
        #filtered food.py
        food_data = [{"Business Name": field['businessName'], "Coords": field['Location']}
            for field in collection2]
        
        for i in range(len(food_data)):
            dataSet.append(food_data[i])

        
        final = []
        for entry in dataSet:
            if entry not in final:
                if entry['Coords'] != '':
                    final.append(entry)

        print(final)

        repo.dropCollection("cma4_tsuen.destinationsProjected")
        repo.createCollection("cma4_tsuen.destinationsProjected")
        repo['cma4_tsuen.destinationsProjected'].insert_many(final)
        repo['cma4_tsuen.destinationsProjected'].metadata({'complete':True})
        print(repo['cma4_tsuen.destinationsProjected'].metadata())

        repo.logout()

        endTime = datetime.datetime.now()

        return {"start":startTime, "end":endTime}
    
    @staticmethod
    def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):
        '''
            Create the provenance document describing everything happening
            in this script. Each run of the script will generate a new
            document describing that invocation event.
            '''

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('cma4_tsuen', 'cma4_tsuen')
        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/') # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/') # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont', 'http://datamechanics.io/ontology#') # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/') # The event log.
        doc.add_namespace('destinations', 'http://bostonopendata-boston.opendata.arcgis.com/datasets/')

        this_script = doc.agent('alg:cma4_tsuen#destinations', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})
        resource = doc.entity('dests:ent+food', {'prov:label':'Destinations\' Name and Coords Data', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        get_dests = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        doc.wasAssociatedWith(get_dests, this_script)
        doc.usage(get_dests, resource, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Retrieval'
                  }
                  )

        dests = doc.entity('dat:cma4_tsuen#dests', {prov.model.PROV_LABEL:'Destinations', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(dests, this_script)
        doc.wasGeneratedBy(dests, get_dests, endTime)
        doc.wasDerivedFrom(dests, resource, get_dests, get_dests, get_dests)

        repo.logout()
                  
        return doc

projectDestinationData.execute()
doc = projectDestinationData.provenance()
print(doc.get_provn())
print(json.dumps(json.loads(doc.serialize()), indent=4))

## eof