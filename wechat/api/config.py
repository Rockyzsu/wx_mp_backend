import json
import os
def get_config():
    root = os.path.dirname(os.path.abspath(__file__))
    file = os.path.join(root,'configuration.json')
    with open(file,'r',encoding='utf8') as fp:
        js_data =json.load(fp)
        return js_data