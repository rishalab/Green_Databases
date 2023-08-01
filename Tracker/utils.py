import os
import psutil
import json
import pandas as pd
import warnings
import requests
import sys
sys.path.insert(0, ".\hardware")
from cpu_metrics import all_available_cpu


class NotNeededExtensionError(Exception):
    pass

class NoCountryCodeError(Exception):
    pass

# prints all the available CPU devices
def available_devices():
    all_available_cpu()
    # need to add RAM


def is_file_opened(needed_file):
   # This function checks if given file is opened in any python or jupyter process
    result = False
    needed_file = os.path.abspath(needed_file)
    python_processes = []
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=["name", "cpu_percent", "pid"])
            if "python" in pinfo["name"].lower() or "jupyter" in pinfo["name"].lower():
                python_processes.append(pinfo["pid"])
                flist = proc.open_files()
                if flist:
                    for nt in flist:
                        if needed_file in nt.path:
                            result = True
        except:
            pass
    return result


'''     This function get an IP of user, defines country and region.
        Then, it searchs user emission level by country and region in the emission level database.
        If there is no certain country, then it returns worldwide constant. 
        If there is certain country in the database, but no certain region, 
        then it returns average country emission level. 
        User can define own emission level and country, using the alpha2 country code.'''
def define_carbon_index(emission_level=None, alpha_2_code=None, region=None):
    if alpha_2_code is None and region is not None:
        raise NoCountryCodeError("In order to set 'region' parameter, 'alpha_2_code' parameter should be set")
    carbon_index_table_name = '.\data\carbon_index.csv'
    if alpha_2_code is None:
        try:
            ip_dict = eval(requests.get("https://ipinfo.io/").content)
        except:
            ip_dict = eval(requests.get("https://ipinfo.io/").content.decode('ascii'))
        country = ip_dict['country']
        region = ip_dict['region']
    else:
        country = alpha_2_code
    if emission_level is not None:
        return (emission_level, f'({country}/{region})') if region is not None else (emission_level, f'({country})')
    data = pd.read_csv(carbon_index_table_name)
    result = data[data['alpha_2_code'] == country]
    if result.shape[0] < 1:
        result = data[data['country'] == 'World']
    elif result.shape[0] > 1 and region is None:
        result = result[result['region'] == 'Whole country']
    elif result.shape[0] > 1:
        if result[result['region'] == region].shape[0] > 0:
            result = result[result['region'] == region]
        else: 
            flag = False
            for alternative_names in data[data['alpha_2_code'] == country]["alternative_name"].values:
                if (
                    type(alternative_names) is str and 
                    region.lower() in alternative_names.lower().split(',') and 
                    region != ""
                ):
                    flag = True
                    result = data[data['alternative_name'] == alternative_names]
            
            if flag is False:
                warnings.warn(
                    message=f"""
    Your 'region' parameter value, which is '{region}', is not found in our region database for choosed country. 
    Please, check, if your region name is written correctly
    """
                )
                result = result[result['region'] == 'Whole country']
    result = result.values[0][-1]
    return (result, f'{country}/{region}') if region is not None else (result, f'{country}')


# This function sets default Tracker attributes values to the file.
def set_params(**params):
    dictionary = dict()
     # filename = resource_stream('SE_TOOL', 'data/config.txt').name
    filename='data/config.txt'
    for param in params:
        dictionary[param] = params[param]
    if "project_name" not in dictionary:
        dictionary["project_name"] = "default project name"
    if "experiment_description" not in dictionary:
        dictionary["experiment_description"] = "default experiment description"
    if "file_name" not in dictionary:
        dictionary["file_name"] = "emission.csv"
    if "measure_period" not in dictionary:
        dictionary["measure_period"] = 10
    if "pue" not in dictionary:
        dictionary["pue"] = 1
    with open(filename, 'w') as json_file:  # store all project details in config.txt
        json_file.write(json.dumps(dictionary))


# This function returns default Tracker attributes values:
def get_params():
    # filename = resource_stream('SE_TOOL', 'data/config.txt').name
    filename='data/config.txt'
    if not os.path.isfile(filename):
        with open(filename, "w"):
            pass
    with open(filename, "r") as json_file:
        if os.path.getsize(filename):
            dictionary = json.loads(json_file.read())
        else:
            dictionary = {
                "project_name": "project name",
                "file_name": "emission.csv",
                "measure_period": 10,
                "pue": 1,
                }
    return dictionary
