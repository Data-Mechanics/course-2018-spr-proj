import urllib.request
import json
import dml
import prov.model
import datetime
import uuid
import geojson

"""
Finds average point (lat, long) for each street in each district where crimes existed.
This is for finding the "middle" of the street - used in findCrimeStats.

Yields the form {DISTRICT: {"street1": {Lat: #, Long: #}, "street2": {Lat: #, Long: #} ...}, DISTRICT2:...}

- Filters out empty entries

"""

def merge_dicts(x, y):
    ''' Helper function to merge 2 dictionaries '''
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z


class transformCrimesData(dml.Algorithm):
    contributor = 'janellc_rstiffel_yash'
    reads = ['janellc_rstiffel.openSpace']
    writes = ['janellc_rstiffel.districtAvgAcres']

    @staticmethod
    def execute(trial = False):
        '''Retrieve some data sets (not using the API here for the sake of simplicity).'''
        startTime = datetime.datetime.now()

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('janellc_rstiffel_yash', 'janellc_rstiffel_yash')

        # Get Crime data
        crimesData = repo.janellc_rstiffel_yash.crimesData.find()

        crimes_dist = {}
        for crime in crimesData:
            # Filters out empty rows
            if (crime['_id'] == None or crime['Long'] == None or crime['Lat'] == None or crime['DISTRICT'] == None or crime['STREET'] == None or "." in crime['STREET']):
                continue
            
            # Store in dictionary here
            if crime['DISTRICT'] not in crimes_dist:
                crimes_dist[crime['DISTRICT']] = {crime['STREET']:{'Lat':float(crime['Lat']),'Long': float(crime['Long']), 'Count':1}}
            else:
                street = crime['STREET']  
                if street not in crimes_dist[crime['DISTRICT']]:
                    d2={crime['STREET']:{'Lat':float(crime['Lat']), 'Long':float(crime['Long']), 'Count':1}}
                    crimes_dist[crime['DISTRICT']] = merge_dicts(crimes_dist[crime['DISTRICT']],d2)
                else:
                    crimes_dist[crime['DISTRICT']][street]['Lat'] += float(crime['Lat'])
                    crimes_dist[crime['DISTRICT']][street]['Long'] += float(crime['Long'])
                    crimes_dist[crime['DISTRICT']][street]['Count'] += 1

        #Calculate the averages here
        for k1, v1 in crimes_dist.items():
            for k2,v2 in v1.items():
                #print(crimes_dist[k1])
                new_lat = crimes_dist[k1][k2]['Lat'] / crimes_dist[k1][k2]['Count']
                new_long = crimes_dist[k1][k2]['Long'] / crimes_dist[k1][k2]['Count']
                crimes_dist[k1][k2] = {'Lat': new_lat, 'Long': new_long}
        
        # Store in DB
        repo.dropCollection("crimeDistricts")
        repo.createCollection("crimeDistricts")

        for key,value in crimes_dist.items():
             r = {key:value}
             repo['janellc_rstiffel_yash.crimeDistricts'].insert(r)
        repo['janellc_rstiffel_yash.crimeDistricts'].metadata({'complete':True})
        print(repo['janellc_rstiffel_yash.crimeDistricts'].metadata())


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
        repo.authenticate('janellc_rstiffel', 'janellc_rstiffel')
        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/janellc_rstiffel/') # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/janellc_rstiffel/') # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont', 'http://datamechanics.io/ontology#') # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/') # The event log.

        
        # Agent, entity, activity
        this_script = doc.agent('alg:janellc_rstiffel#transformOpenSpace', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})
        # Two resources: openSpace and zipCodes
        resource1 = doc.entity('dat:janellc_rstiffel#openSpace', {'prov:label':'311, Service Requests', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'geojson'})
        resource2 = doc.entity('dat:janellc_rstiffel#zipCodes', {'prov:label':'311, Service Requests', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        
        transform_openSpace = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        doc.wasAssociatedWith(transform_openSpace, this_script)

        doc.usage(transform_openSpace, resource1, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Calculation',
                  'ont:Query':''
                  }
                  )
        doc.usage(transform_openSpace, resource2, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Calculation',
                  'ont:Query':''
                  }
                  )

        districtAvgAcres = doc.entity('dat:janellc_rstiffel#districtAvgAcres', {prov.model.PROV_LABEL:'District Avg Results', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(districtAvgAcres, this_script)
        doc.wasGeneratedBy(districtAvgAcres, transform_openSpace, endTime)
        doc.wasDerivedFrom(districtAvgAcres, resource1, transform_openSpace, transform_openSpace, transform_openSpace)
        doc.wasDerivedFrom(districtAvgAcres, resource2, transform_openSpace, transform_openSpace, transform_openSpace)

        repo.logout()
                  
        return doc

transformCrimesData.execute()
# doc = transformOpenSpace.provenance()
# print(doc.get_provn())
# print(json.dumps(json.loads(doc.serialize()), indent=4))

## eof
