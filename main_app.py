import time
import mysql.connector
from pymongo import MongoClient
import re
# Tracker where all metric calculation functions are implemented
from Tracker.main import Tracker
import os
from flask import Flask, render_template, request, Blueprint
from werkzeug.utils import secure_filename
import glob
import fileinput
import sys
import matplotlib.pyplot as plt
import io
import base64
sys.path.insert(0, "./")
sys.path.insert(0, "./")


app = Flask(__name__)
os.makedirs(os.path.join(app.instance_path, 'uploads'), exist_ok=True)


@app.route("/")
def index():
    return render_template('ecodb.html')


# ----------------- EcoDB routes and Definitions ---------------

@app.route('/ecodb', methods=['POST'])
def ecodb():
    return render_template('ecodb.html')


@app.route('/comparision')
def comparision():
    return render_template('comparision.html')


@app.route('/execute_query')
def execute_query():
    return render_template('query_home.html')


@app.route('/compare', methods=['POST'])
def compare():
    sql_query = request.form['sql_query']
    sql_db_name = request.form['sql_db_name']
    password = request.form['password']
    nosql_query = request.form['nosql_query']
    nosql_db_name = request.form['nosql_db_name']
    sql_res = execute_sql_query(sql_query, 'root', password, sql_db_name)
    time.sleep(1)
    nosql_res = execute_noSQL_query(nosql_query, nosql_db_name)
    eff_res = []
    for i in range(2, 4):
        if sql_res[i] < nosql_res[i]:
            eff_res.append("SQL")
        else:
            eff_res.append("NOSQL")
    if sql_res[4] > nosql_res[4]:
        eff_res.append(nosql_res[4])
    else:
        eff_res.append(sql_res[4])
    if sql_res[5] > nosql_res[5]:
        eff_res.append(nosql_res[5])
    else:
        eff_res.append(sql_res[5])
    return render_template('compare_result.html', sql_cpu_consumption=sql_res[0], sql_ram_consumption=sql_res[1], sql_total_consumption=sql_res[2], sql_co2_emissions=sql_res[3], sql_miles_equvivalence=sql_res[4], sql_tv_equvivalence=sql_res[5],
                           nosql_cpu_consumption=nosql_res[0], nosql_ram_consumption=nosql_res[1], nosql_total_consumption=nosql_res[
                               2], nosql_co2_emissions=nosql_res[3], nosql_miles_equvivalence=nosql_res[4], nosql_tv_equvivalence=nosql_res[5],
                           efficient_total_consumption=eff_res[0], efficient_co2_emissions=eff_res[1], mile_eqivalents=eff_res[2], tv_minutes=eff_res[3])


@app.route('/details', methods=['POST'])
def execute_query_helper():
    query = request.form['query']
    if len(query) == 0:
        not_query = 'Please enter your query.'
        return render_template('ecodb.html', not_query=not_query)
    elif is_sql(query):
        lang = "SQL"
        return render_template('sql_details.html', query=query, lang=lang)
    elif is_nosql(query):
        lang = "NoSQL"
        return render_template('nosql_details.html', query=query, lang=lang)
    else:
        not_query = 'Please enter a valid query.'
        return render_template('ecodb.html', not_query=not_query)


@app.route('/display', methods=['POST'])
def display1():
    lang = request.form['lang']
    query = request.form['query']
    if lang == "SQL":
        password = request.form['password']
        db_name = request.form['db_name']
        res = execute_sql_query(query, 'root', password, db_name)
    else:
        db_name = request.form['db_name']
        res = execute_noSQL_query(query, db_name)

    return render_template('ecodb_result.html', cpu_consumption=res[0], ram_consumption=res[1], total_consumption=res[2], co2_emissions=res[3], mile_eqivalents=res[4], tv_minutes=res[5])


'''
@desc : 8.89 * 10-3 metric tons CO2/gallon gasoline *
        1/22.0 miles per gallon car/truck average *
        1 CO2, CH4, and N2O/0.988 CO2 = 4.09 x 10-4 metric tons CO2E/mile

@Source : EPA

done by Namitha
'''


def carbon_to_miles(kg_carbon):

    f_carbon = float(kg_carbon)
    res = 4.09 * 10**(-7) * f_carbon
    return "{:.2e}".format(res)  # number of miles driven by avg car


'''
@desc :  Gives the amount of minutes of watching a 32-inch LCD flat screen tv required to emit and
         equivalent amount of carbon. Ratio is 0.097 kg CO2 / 1 hour tv

@Source : EPA

done by Namitha
'''


def carbon_to_tv(kg_carbon):

    f_carbon = float(kg_carbon)
    res = f_carbon * (1 / .097) * 60
    return "{:.2e}".format(res)


'''
@input : String  - given query 
@output: Boolean - True - SQL       
@desc  : detects whether given query is SQL or not

done by Poojasree
'''


def is_sql(query):
    sql_keywords = ["SELECT", "UPDATE", "DELETE", "INSERT INTO" "FROM", "WHERE", "JOIN", "INNER JOIN",
                    "LEFT JOIN", "RIGHT JOIN", "ON", "GROUP BY", "HAVING", "ORDER BY", "LIMIT", "DESCRIBE"]
    for keyword in sql_keywords:
        if re.search(r"\b" + keyword + r"\b", query.upper()):
            return True
    return False


'''
@input : String  - given query 
@output: Boolean - True - NoSQL     
@desc  : detects whether given query is NoSQL or not

done by Manasa
'''


def is_nosql(query):
    nosql_keywords = ["insertOne", "insertMany", "find", "findOne",
                      "updateOne", "updateMany", "deleteOne", "deleteMany"]
    split_query = query.split('.')
    idx = split_query[2].find("(")
    key = split_query[2][:idx]
    if split_query[0] == "db" and len(split_query) > 2:
        if key in nosql_keywords:
            return True
    return False


'''
@input : String - query , String : db_name
@output: Array consists of query energy consumption by CPU,RAM and CO2 emissions
@desc  : calculates the cpu,ram consumptions and CO2 emissions of SQL query by initializing a tracker object just before the start of the query execution and the object stops at the end of query execution

done by Manasa and Namitha
'''


def execute_sql_query(query, db_user, db_password, db_name):
    obj = Tracker()
    # Tracker object starts to calculate the cpu,ram consumptions
    obj.start()
    res = []
    connection = mysql.connector.connect(
        user=db_user, password=db_password, host='localhost', database=db_name)
    cursor = connection.cursor()
    cursor.execute(query)
    splitted_query = query.upper().split()
    if splitted_query[0] == "DELETE" or splitted_query[0] == "UPDATE" or (splitted_query[0] == "INSERT" and splitted_query[1] == "INTO"):
        connection.commit()  # commit the changes
        connection.close()
    else:
        result_set = cursor.fetchall()
        print(result_set)
        connection.close()
    # Tracker object stops
    obj.stop()

    # store the cpu and ram consumptions,CO2 emissions
    res.append("{:.2e}".format(obj.cpu_consumption()))
    res.append("{:.2e}".format(obj.ram_consumption()))
    res.append("{:.2e}".format(obj.consumption()))
    CO2_emissions = obj._construct_attributes_dict()['CO2_emissions(kg)'][0]
    res.append("{:.2e}".format(float(CO2_emissions)))
    res.append(carbon_to_miles(
        obj._construct_attributes_dict()['CO2_emissions(kg)'][0]))
    res.append(carbon_to_tv(
        obj._construct_attributes_dict()['CO2_emissions(kg)'][0]))
    return res


'''
@input : String - query , String : db_name
@output: Array consists of query energy consumption by CPU,RAM and CO2 emissions
@desc  : calculates the cpu,ram consumptions and CO2 emissions of MongoDB query by initializing a tracker object just before the start of the query execution and the object stops at the end of query execution

done by Poojasree
'''


def execute_noSQL_query(query, db_name):
    client = MongoClient('mongodb://localhost:27017/')
    obj = Tracker()
    # Tracker object starts to calculate the cpu,ram consumptions
    obj.start()
    res = []

    # split the query string as [db,collection,query_field]
    splitted_query = query.split('.')
    collection_name = splitted_query[1]

    db = client[db_name]
    collection = db[collection_name]
    query_field = splitted_query[2]

    # store aggregate functions like count(),sort() in additonal_funcs
    additional_funcs = []
    if len(splitted_query) > 3:
        for i in range(3, len(splitted_query)):
            additional_funcs.append(splitted_query[i])
            print(splitted_query[i])

    # executes the query operation from the query_field
    if "insertOne" in query_field:
        print("inserting one document")
        query_doc = query_field.split('insertOne(')[1].split(')')[0]
        split_quer_doc = query_doc.split(',')
        arg_dict = []
        for q in split_quer_doc:
            arg_dict.append(eval(q))

        result = collection.insert_one(*arg_dict)
        print(result)

    if "insertMany" in query_field:
        print("inserting many documents")
        query_doc = query_field.split('insertMany(')[1].split(')')[0]
        split_quer_doc = query_doc.split(',')
        arg_dict = []
        for q in split_quer_doc:
            arg_dict.append(eval(q))

        result = collection.insert_many(*arg_dict)
        print(result)

    if "find" in query_field:
        print("finding documents")
        query_doc = query_field.split('find(')[1].split(')')[0]
        print(query_doc)
        if query_doc == '':
            print("no doc")
            result = collection.find()
            print(result)
        else:
            split_quer_doc = query_doc.split(',')
            arg_dict = []
            for q in split_quer_doc:
                arg_dict.append(eval(q))

            result = collection.find(*arg_dict)
            print(result)

    if "findOne" in query_field:
        print("finding documents")
        query_doc = query_field.split('findOne(')[1].split(')')[0]
        split_quer_doc = query_doc.split(',')
        arg_dict = []
        for q in split_quer_doc:
            arg_dict.append(eval(q))

        result = collection.find_one(*arg_dict)

    if "updateOne" in query_field:
        print("update one document")
        query_doc = query_field.split('updateOne(')[1].split(')')[0]
        split_quer_doc = query_doc.split(',')
        # print(split_quer_doc)
        arg_dict = []
        for q in split_quer_doc:
            arg_dict.append(eval(q))

        result = collection.update_one(*arg_dict)
        print(result.modified_count)

    if "updateMany" in query_field:
        print("update one document")
        query_doc = query_field.split('updateMany(')[1].split(')')[0]
        split_quer_doc = query_doc.split(',')
        arg_dict = []
        for q in split_quer_doc:
            arg_dict.append(eval(q))

        result = collection.update_many(*arg_dict)
        print(result.modified_count)

    if "deleteOne" in query_field:
        print("deleting one document")
        query_doc = query_field.split('deleteOne(')[1].split(')')[0]
        split_quer_doc = query_doc.split(',')
        arg_dict = []
        for q in split_quer_doc:
            arg_dict.append(eval(q))

        result = collection.delete_one(*arg_dict)
        print(result)

    if "deleteMany" in query_field:
        print("deleting many documents")
        query_doc = query_field.split('deleteMany(')[1].split(')')[0]
        split_quer_doc = query_doc.split(',')
        arg_dict = []
        for q in split_quer_doc:
            arg_dict.append(eval(q))

        result = collection.delete_many(*arg_dict)
        print(result)

    client.close()
    # Tracker object stops
    obj.stop()

    # store the cpu and ram consumptions,CO2 emissions
    res.append("{:.2e}".format(obj.cpu_consumption()))
    res.append("{:.2e}".format(obj.ram_consumption()))
    res.append("{:.2e}".format(obj.consumption()))
    CO2_emissions = obj._construct_attributes_dict()['CO2_emissions(kg)'][0]
    res.append("{:.2e}".format(float(CO2_emissions)))
    res.append(carbon_to_miles(
        obj._construct_attributes_dict()['CO2_emissions(kg)'][0]))
    res.append(carbon_to_tv(
        obj._construct_attributes_dict()['CO2_emissions(kg)'][0]))
    return res


'''
main program
'''
if __name__ == '__main__':
    app.run(debug=True)
