import json
from unicodedata import normalize

#ok so first we need to process the terpenes
terpene_result = []
with open(f"extracts/Terpene.json", "r") as f:
    json_data = json.loads(f.read())
    for key in json_data.keys():
        res = {k.lower():v for k,v in json_data[key].items()}
        res['name']=key
        if 'description' not in res:
            res['description'] = f"A terpene containing the following aromas ({','.join(res['aromas'])}) and the following effects ({','.join(res['aromas'])})"
        terpene_result.append(res)

with open("extracts/terpene.ios.json", "w") as f:
    f.write(json.dumps(terpene_result))
strain_result =[]
terpenes = [x['name'] for x in terpene_result]
with open ("extracts/strain_data.json") as f:
    json_data = json.loads(f.read())
    for key in json_data.keys():
        res = {k.lower():v for k,v in json_data[key].items()}
        res['name'] = key
        if 'type' not in res:
            print(f"{res['name']} was missing type")
            res['type']='Hybrid'
        if 'image' not in res:
            print(f"{res['name']} was missing image")
            res['image']=''
        # if 'description' not in res:
        #     res[
        #         'description'] = f"A terpene containing the following aromas ({','.join(res['aromas'])}) and the following effects ({','.join(res['aromas'])})"
        #fix the terpenes
        for i in range(0, len(json_data[key]['terpenes'])):
            for terp in terpenes:
                if terp.lower() in json_data[key]['terpenes'][i].lower():
                    json_data[key]['terpenes'][i]=terp
            pass
        strain_result.append(res)
# strain_result=strain_result[100:]
with open("/Users/andrew/Downloads/strain_data.json", "w+") as f:
    # endoded_string =json.dumps(strain_result[:1000], ensure_ascii=False)
    # f.write(endoded_string.decode())
    f.write(json.dumps(strain_result[:2000], ensure_ascii=False))