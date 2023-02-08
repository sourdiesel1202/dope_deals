import json
import traceback
import urllib
import requests
states = json.loads("""{"Alabama": {"code": "AL", "legal": false}, "Alaska": {"code": "AK", "legal": true}, "American Samoa": {"code": "AS", "legal": false}, "Arizona": {"code": "AZ", "legal": true}, "Arkansas": {"code": "AR", "legal": false}, "California": {"code": "CA", "legal": true}, "Colorado": {"code": "CO", "legal": true}, "Connecticut": {"code": "CT", "legal": true}, "Delaware": {"code": "DE", "legal": false}, "District Of Columbia": {"code": "DC", "legal": true}, "Federated States Of Micronesia": {"code": "FM", "legal": false}, "Florida": {"code": "FL", "legal": false}, "Georgia": {"code": "GA", "legal": false}, "Guam": {"code": "GU", "legal": true}, "Hawaii": {"code": "HI", "legal": false}, "Idaho": {"code": "ID", "legal": false}, "Illinois": {"code": "IL", "legal": true}, "Indiana": {"code": "IN", "legal": false}, "Iowa": {"code": "IA", "legal": false}, "Kansas": {"code": "KS", "legal": false}, "Kentucky": {"code": "KY", "legal": false}, "Louisiana": {"code": "LA", "legal": false}, "Maine": {"code": "ME", "legal": true}, "Marshall Islands": {"code": "MH", "legal": false}, "Maryland": {"code": "MD", "legal": true}, "Massachusetts": {"code": "MA", "legal": true}, "Michigan": {"code": "MI", "legal": true}, "Minnesota": {"code": "MN", "legal": false}, "Mississippi": {"code": "MS", "legal": false}, "Missouri": {"code": "MO", "legal": true}, "Montana": {"code": "MT", "legal": true}, "Nebraska": {"code": "NE", "legal": false}, "Nevada": {"code": "NV", "legal": true}, "New Hampshire": {"code": "NH", "legal": false}, "New Jersey": {"code": "NJ", "legal": true}, "New Mexico": {"code": "NM", "legal": true}, "New York": {"code": "NY", "legal": true}, "North Carolina": {"code": "NC", "legal": false}, "North Dakota": {"code": "ND", "legal": false}, "Northern Mariana Islands": {"code": "MP", "legal": false}, "Ohio": {"code": "OH", "legal": false}, "Oklahoma": {"code": "OK", "legal": false}, "Oregon": {"code": "OR", "legal": true}, "Palau": {"code": "PW", "legal": false}, "Pennsylvania": {"code": "PA", "legal": false}, "Puerto Rico": {"code": "PR", "legal": false}, "Rhode Island": {"code": "RI", "legal": true}, "South Carolina": {"code": "SC", "legal": false}, "South Dakota": {"code": "SD", "legal": false}, "Tennessee": {"code": "TN", "legal": false}, "Texas": {"code": "TX", "legal": false}, "Utah": {"code": "UT", "legal": false}, "Vermont": {"code": "VT", "legal": true}, "Virgin Islands": {"code": "VI", "legal": false}, "Virginia": {"code": "VA", "legal": true}, "Washington": {"code": "WA", "legal": true}, "West Virginia": {"code": "WV", "legal": false}, "Wisconsin": {"code": "WI", "legal": false}, "Wyoming": {"code": "WY", "legal": false}}""")
cites = {}
for state in states.keys():
    where = urllib.parse.quote_plus("""
    {
        "population": {
            "$gt": 200
        }
    }
    """)
    url = f'https://parseapi.back4app.com/classes/{states[state]["code"]}?limit=2000&where=%s' % where
    headers = {
        'X-Parse-Application-Id': 'YV6GTTBZe2seEMboA5c44F9eXledturUyBFmQwkD',  # This is the fake app's application id
        'X-Parse-Master-Key': 'WCx4AtqgKzDpQllBdBqeBqlpEzlr5EhfRWSbeI0n'  # This is the fake app's readonly master key
    }
    r = requests.get(url,verify=False, headers=headers)
    try:
        data = json.loads(r.content.decode('utf-8')) # Here you have the data that you need
        print(f"Found {len(data['results'])} cities in {state}")
        for city_dict in data['results']:
            cites[f"{city_dict['name']}:{city_dict['adminCode']}"]={"name":city_dict['name'], "state":city_dict['adminCode']}
        with open(f"cities.json", 'w') as f:
            f.write(json.dumps(cites))
    except:
        traceback.print_exc()
        print(f"Could not load data for state: {state}")
    # print(json.dumps(data, indent=2))
