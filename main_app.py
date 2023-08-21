import time
import csv
import mysql.connector
from pymongo import MongoClient
import re
# Tracker where all metric calculation functions are implemented
from Tracker.main import Tracker
import os
from flask import Flask, render_template, request, Blueprint, session
from werkzeug.utils import secure_filename
import glob
import fileinput
import sys
import matplotlib.pyplot as plt
import io
import base64
import psycopg2
import uuid
import couchbase
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions, QueryOptions
from couchbase.management.buckets import BucketSettings, CreateBucketSettings
from couchbase.exceptions import BucketNotFoundException
from couchbase.n1ql import N1QLQuery
#from couchbase.cluster import BucketType
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, "./")
sys.path.insert(0, "./")


app = Flask(__name__)
app.secret_key = 'secret'
# os.makedirs(os.path.join(app.instance_path, 'uploads'), exist_ok=True)


@app.route("/")
def index():
    return render_template('ecodb.html')


@app.route("/upload_file", methods=['GET', 'POST'])
def upload_file():
    return render_template('upload.html')


def allowed_file(filename):
    print(filename.rsplit('.', 1)[1].lower())
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'


@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        f = request.files
        print(f'this {f}')
        f = request.files['file']
        filename = f.filename
        session['filename'] = filename
        filename1 = filename.split(".")
        table_name = filename1[0].replace(" ", "_")
        session['table_name'] = table_name
        # if no file is found then display the error please upload a file
        if f.filename == '':
            not_uploaded = 'Please select a file to upload.'
            return render_template('upload.html', not_uploaded=not_uploaded)
        # if file is in correct format then upload it to the uploaded folder

        if f and allowed_file(f.filename):
            upload_folder = 'uploads'
            empty_folder(upload_folder)
            fp = os.path.join('uploads', f.filename)
            f.save(fp)

            # Check if the file exists before opening it
            if os.path.isfile(fp):
                # Read the first row of the CSV file and print it
                with open(fp, 'r') as csv_file:
                    csv_reader = csv.reader(csv_file)
                    data = list(csv_reader)
                    column_names = data[0]
                    column_names = [replace_spaces_with_underscore(
                        item) for item in column_names]
                    session['column_names'] = column_names
                    new_data = data[1:]
                    new_fp = os.path.join('uploads', "new_"+f.filename)
                    with open(new_fp, 'w', newline='') as new_csv_file:
                        csv_writer = csv.writer(new_csv_file)
                        csv_writer.writerows(new_data)
                os.remove(fp)
                os.rename(new_fp, fp)
                return render_template('column_names.html', items=column_names)
            else:
                return "File not found."


def empty_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")


@app.route('/table_creation', methods=['POST'])
def table_creation():
    # return render_template('comparision.html')
    mysql_username = request.form['mysql_username']
    mysql_db_name = request.form['mysql_db_name']
    mysql_password = request.form['mysql_password']
    mongodb_db_name = request.form['mongodb_db_name']
    postgresql_username = request.form['postgresql_username']
    postgresql_db_name = request.form['postgresql_db_name']
    postgresql_password = request.form['postgresql_password']
    couchbase_username = request.form['couchbase_username']
    couchbase_password = request.form['couchbase_password']

    session['mysql_username'] = mysql_username
    session['mysql_db_name'] = mysql_db_name
    session['mysql_password'] = mysql_password
    session['mongodb_db_name'] = mongodb_db_name
    session['postgresql_username'] = postgresql_username
    session['postgresql_db_name'] = postgresql_db_name
    session['postgresql_password'] = postgresql_password
    session['couchbase_username'] = couchbase_username
    session['couchbase_password'] = couchbase_password

    a = create_mysql_table(mysql_username, mysql_password, mysql_db_name)
    b = create_mongodb_collection(mongodb_db_name)
    c = create_postgresql_table(postgresql_username,
                                postgresql_password, postgresql_db_name)
    d = create_couchbase_collection(
        couchbase_username, couchbase_password)
    if a == 'success' and b == 'success' and c == 'success' and d == 'success':
        return render_template('enter_queries.html')
    else:
        return "Unsuccessfull!"


@app.route('/submit_columns', methods=['POST'])
def submit_columns():
    column_names = session.get('column_names', None)
    column_types = [request.form.get(item) for item in column_names]
    primary_key = request.form.get('primary_key')
    primary_key = primary_key.replace(" ", "_")
    session['primary_key'] = primary_key
    session['column_types'] = column_types
    return render_template('input.html')


def replace_spaces_with_underscore(item):
    return item.replace(" ", "_")


def create_mysql_table(user, password, database):
    conn = mysql.connector.connect(
        host="localhost", user=user, passwd=password, database=database)
    cur = conn.cursor()
    column_names = session.get('column_names', None)
    column_types = session.get('column_types', None)
    filename = session.get('filename', None)
    table_name = session.get('table_name', None)
    primary_key = session.get('primary_key', None)

    columns = [(x, y) for x, y in zip(column_names, column_types)]
    date_columns = []
    for column_name, column_type in columns:
        if column_type == 'date':
            date_columns.append(column_name)

    drop_query = f'DROP TABLE IF EXISTS {table_name};'
    create_query = f'CREATE TABLE {table_name} ('
    for column_name, column_type in columns:
        create_query += f'{column_name} {column_type}, '
    # Remove the trailing comma and space
    create_query = create_query[:-2]

    if primary_key:
        create_query += f', PRIMARY KEY ({primary_key})'

    create_query += ');'
    path = 'uploads\\' + filename
    data = csv.reader(open(path))
    insert_query = f'INSERT INTO {table_name} ('
    for x in column_names:
        insert_query += f'{x}, '
    insert_query = insert_query[:-2]
    insert_query += f') VALUES ('
    placeholders = ', '.join(['%s'] * len(column_names))
    insert_query += placeholders
    insert_query += f')'

    # print(drop_query)
    # print(create_query)
    # print(insert_query)
    cur.execute(drop_query)
    cur.execute(create_query)
    for row in data:
        cur.execute(insert_query, row)
        # print(row)

    # for row in data:
    #     # Parse and reformat date columns if necessary
    #     for i, column_name in enumerate(column_names):
    #         if column_name in date_columns:
    #             try:
    #                 # Assuming the date format is 'dd-mm-yyyy' in the CSV file
    #                 date_str = row[i]
    #                 date_obj = datetime.strptime(date_str, '%d-%m-%Y')
    #                 formatted_date = date_obj.strftime('%Y-%m-%d')
    #                 row[i] = formatted_date
    #             except ValueError as e:
    #                 # print(f"Error parsing date: {e}")
    #                 pass
    #     cur.execute(insert_query, row)

    conn.commit()
    cur.close()
    conn.close()
    print('Table created and data inserted in MySQL.')
    return "success"


def create_postgresql_table(user, password, database):
    conn = psycopg2.connect(
        host="localhost", user=user, password=password, database=database)
    cur = conn.cursor()
    column_names = session.get('column_names', None)
    column_types = session.get('column_types', None)
    filename = session.get('filename', None)
    table_name = session.get('table_name', None)
    primary_key = session.get('primary_key', None)

    columns = [(x, y) for x, y in zip(column_names, column_types)]
    date_columns = []
    for column_name, column_type in columns:
        if column_type == 'date':
            date_columns.append(column_name)

    drop_query = f'DROP TABLE IF EXISTS {table_name};'
    create_query = f'CREATE TABLE {table_name} ('
    for column_name, column_type in columns:
        if column_name == primary_key:
            create_query += f'{column_name} {column_type} PRIMARY KEY, '
        else:
            create_query += f'{column_name} {column_type}, '
    # Remove the trailing comma and space
    create_query = create_query[:-2]

    create_query += ');'
    path = 'uploads\\' + filename
    data = csv.reader(open(path))
    insert_query = f'INSERT INTO {table_name} ('
    for x in column_names:
        insert_query += f'{x}, '
    insert_query = insert_query[:-2]
    insert_query += f') VALUES ('
    placeholders = ', '.join(['%s'] * len(column_names))
    insert_query += placeholders
    insert_query += f')'

    # print(drop_query)
    # print(create_query)
    # print(insert_query)
    cur.execute(drop_query)
    cur.execute(create_query)
    for row in data:
        cur.execute(insert_query, row)
        # print(row)

    conn.commit()
    cur.close()
    conn.close()
    print('Table created and data inserted in PostgreSQL.')
    return "success"


def create_mongodb_collection(db_name):
    client = MongoClient('mongodb://localhost:27017/')

    collection_name = session.get('table_name', None)
    column_names = session.get('column_names', None)
    column_types = session.get('column_types', None)
    columns = [(x, y) for x, y in zip(column_names, column_types)]
    filename = session.get('filename', None)

    db = client[db_name]

    if collection_name in db.list_collection_names():
        db.drop_collection(collection_name)

    collection = db[collection_name]

    path = 'uploads/' + filename
    with open(path, 'r') as file:
        reader = csv.DictReader(file, fieldnames=column_names)
        for row in reader:
            # Convert column values to the specified types before inserting
            converted_row = {}
            for col_name, col_type in zip(column_names, column_types):
                value = row[col_name]
                if col_type == 'int':
                    converted_row[col_name] = int(row[col_name])
                elif col_type == 'float':
                    converted_row[col_name] = float(row[col_name])
                elif col_type == 'bool':
                    converted_row[col_name] = row[col_name].lower() == 'true'
                elif col_type == 'date':
                    converted_row[col_name] = datetime.strptime(
                        value, '%d-%m-%y')
                else:
                    converted_row[col_name] = row[col_name]

            # Insert the converted row into the collection
            collection.insert_one(converted_row)
    print('Collection created and data inserted in MongoDB.')
    return "success"


def create_couchbase_collection(user, password):
    try:
        cluster = Cluster('couchbase://localhost',
                          ClusterOptions(PasswordAuthenticator(user, password)))
        auth = PasswordAuthenticator(user, password)
        conn = Cluster.connect('couchbase://localhost', ClusterOptions(auth))

        # Get the column names, types, and primary key from the session
        column_names = session.get('column_names', None)
        column_types = session.get('column_types', None)
        filename = session.get('filename', None)
        bucket_name = session.get('table_name', None)
        primary_key = session.get('primary_key', None)

        existing_buckets = cluster.buckets().get_all_buckets()

        if bucket_name in [bucket.name for bucket in existing_buckets]:
            # If it exists, delete it
            cluster.buckets().drop_bucket(bucket_name)

        # Create a new bucket with the same name
        settings = CreateBucketSettings(
            name=bucket_name,
            bucket_type='couchbase',
            ram_quota_mb=100,
            num_replicas=1
        )
        cluster.buckets().create_bucket(settings)

        time.sleep(2)

        bucket = cluster.bucket(bucket_name)
        collection = bucket.default_collection()

        path = 'uploads/' + filename

        with open(path, 'r') as csv_file:
            # print(path)
            data = csv.reader(csv_file)
            for row in data:
                # Create a dictionary to store the document fields
                doc = {}
                # Loop through the column names and types and assign the values from the row
                for i, (name, type) in enumerate(zip(column_names, column_types)):
                    # Convert the value to the appropriate type
                    if type == 'int':
                        value = int(row[i])
                    elif type == 'float':
                        value = float(row[i])
                    elif type == 'date':
                        value = datetime.strptime(row[i], '%d-%m-%Y').date()
                    else:
                        value = row[i]
                    doc[name] = value

                # Insert the document into Couchbase using a unique document ID
                # Assuming primary_key is the ID field
                document_id = str(doc[primary_key])
                collection.upsert(document_id, doc)
        time.sleep(2)

        query = 'CREATE PRIMARY INDEX ON '
        query += bucket_name
        query += ' USING GSI;'

        res = execute_couchbase_query(query, user, password, bucket_name)
        print('The primary index is ready.')
        print('Bucket created and data inserted in Couchbase.')
        return "success"
    except Exception as e:
        print(f"Error: {str(e)}")


@app.route('/comparision')
def comparision():
    return render_template('comparision.html')


@app.route('/enter_queries', methods=['POST'])
def enter_queries():
    mysql_query = request.form['mysql_query']
    mongodb_query = request.form['mongodb_query']
    postgresql_query = request.form['postgresql_query']
    couchbase_query = request.form['couchbase_query']

    mysql_username = session.get('mysql_username', None)
    mysql_db_name = session.get('mysql_db_name', None)
    mysql_password = session.get('mysql_password', None)

    mongodb_db_name = session.get('mongodb_db_name', None)

    postgresql_username = session.get('postgresql_username', None)
    postgresql_db_name = session.get('postgresql_db_name', None)
    postgresql_password = session.get('postgresql_password', None)

    couchbase_username = session.get('couchbase_username', None)
    couchbase_password = session.get('couchbase_password', None)
    couchbase_bucket_name = session.get('table_name', None)

    time.sleep(1)
    mysql_res = execute_mysql_query(
        mysql_query, mysql_username, mysql_password, mysql_db_name)
    time.sleep(1)
    postgresql_res = execute_postgreSQL_query(
        postgresql_query, postgresql_username, postgresql_password, postgresql_db_name)
    time.sleep(1)
    mongodb_res = execute_mongodb_query(mongodb_query, mongodb_db_name)
    time.sleep(1)
    couchbase_res = execute_couchbase_query(
        couchbase_query, couchbase_username, couchbase_password, couchbase_bucket_name)
    time.sleep(1)
    eff_res = []
    databases = []
    databases.append("MySQl")
    databases.append("PostgreSQl")
    databases.append("Mongodb")
    databases.append("Couchbase")
    databases1 = []
    databases1.append("MySQl")
    databases1.append("PostgreSQl")
    databases1.append("Mongodb")
    databases1.append("Couchbase")
    eff_total_consumption = []
    eff_total_consumption.append(mysql_res[2])
    eff_total_consumption.append(postgresql_res[2])
    eff_total_consumption.append(mongodb_res[2])
    eff_total_consumption.append(couchbase_res[2])

    eff_co2_emissions = []
    eff_co2_emissions.append(mysql_res[3])
    eff_co2_emissions.append(postgresql_res[3])
    eff_co2_emissions.append(mongodb_res[3])
    eff_co2_emissions.append(couchbase_res[3])
    databases_total_dict = {index: name for index,
                            name in zip(eff_total_consumption, databases)}
    databases_co2_dict = {index: name for index,
                          name in zip(eff_co2_emissions, databases1)}
    sorted_total = [databases_total_dict[i]
                    for i in sorted(databases_total_dict, key=lambda x: Decimal(x))]
    sorted_co2 = [databases_co2_dict[j]
                  for j in sorted(databases_co2_dict, key=lambda x: Decimal(x))]
    eff_res.append(sorted_total[0])
    eff_res.append(sorted_co2[0])
    miles = []
    miles.append(mysql_res[4])
    miles.append(postgresql_res[4])
    miles.append(mongodb_res[4])
    miles.append(couchbase_res[4])
    tv = []
    tv.append(mysql_res[5])
    tv.append(postgresql_res[5])
    tv.append(mongodb_res[5])
    tv.append(couchbase_res[5])
    miles.sort()
    tv.sort()
    eff_res.append(miles[0])
    eff_res.append(tv[0])
    return render_template('compare_result.html', mysql_cpu_consumption=mysql_res[0], mysql_ram_consumption=mysql_res[1], mysql_total_consumption=mysql_res[2],
                           mysql_co2_emissions=mysql_res[3], mysql_miles_equvivalence=mysql_res[
                               4], mysql_tv_equvivalence=mysql_res[5],
                           postgresql_cpu_consumption=postgresql_res[0], postgresql_ram_consumption=postgresql_res[
                               1], postgresql_total_consumption=postgresql_res[2],
                           postgresql_co2_emissions=postgresql_res[3], postgresql_miles_equvivalence=postgresql_res[
                               4], postgresql_tv_equvivalence=postgresql_res[5],
                           mongodb_cpu_consumption=mongodb_res[0], mongodb_ram_consumption=mongodb_res[1], mongodb_total_consumption=mongodb_res[
                               2], mongodb_co2_emissions=mongodb_res[3], mongodb_miles_equvivalence=mongodb_res[4], mongodb_tv_equvivalence=mongodb_res[5],
                           couchbase_cpu_consumption=couchbase_res[0], couchbase_ram_consumption=couchbase_res[1], couchbase_total_consumption=couchbase_res[
                               2], couchbase_co2_emissions=couchbase_res[3], couchbase_miles_equvivalence=couchbase_res[4], couchbase_tv_equvivalence=couchbase_res[5],
                           efficient_total_consumption=eff_res[0], efficient_co2_emissions=eff_res[1], mile_eqivalents=eff_res[2], tv_minutes=eff_res[3])


@app.route('/choice')
def choice():
    return render_template('choice.html')


@app.route('/execute_query')
def execute_query():
    return render_template('query_home.html')


@app.route('/compare', methods=['POST'])
def compare():
    mysql_query = request.form['mysql_query']
    mysql_db_name = request.form['mysql_db_name']
    mysql_password = request.form['mysql_password']
    mongodb_query = request.form['mongodb_query']
    mongodb_db_name = request.form['mongodb_db_name']
    postgresql_query = request.form['postgresql_query']
    postgresql_db_name = request.form['postgresql_db_name']
    postgresql_password = request.form['postgresql_password']
    couchbase_query = request.form['couchbase_query']
    couchbase_username = request.form['couchbase_username']
    couchbase_password = request.form['couchbase_password']
    couchbase_bucket_name = request.form['couchbase_bucket_name']

    time.sleep(1)
    mysql_res = execute_mysql_query(
        mysql_query, 'root', mysql_password, mysql_db_name)
    time.sleep(1)
    postgresql_res = execute_postgreSQL_query(
        postgresql_query, 'postgres', postgresql_password, postgresql_db_name)
    time.sleep(1)
    mongodb_res = execute_mongodb_query(mongodb_query, mongodb_db_name)
    time.sleep(1)
    couchbase_res = execute_couchbase_query(
        couchbase_query, couchbase_username, couchbase_password, couchbase_bucket_name)
    time.sleep(1)
    eff_res = []
    databases = []
    databases.append("MySQl")
    databases.append("PostgreSQl")
    databases.append("Mongodb")
    databases.append("Couchbase")
    databases1 = []
    databases1.append("MySQl")
    databases1.append("PostgreSQl")
    databases1.append("Mongodb")
    databases1.append("Couchbase")
    eff_total_consumption = []
    eff_total_consumption.append(mysql_res[2])
    eff_total_consumption.append(postgresql_res[2])
    eff_total_consumption.append(mongodb_res[2])
    eff_total_consumption.append(couchbase_res[2])

    eff_co2_emissions = []
    eff_co2_emissions.append(mysql_res[3])
    eff_co2_emissions.append(postgresql_res[3])
    eff_co2_emissions.append(mongodb_res[3])
    eff_co2_emissions.append(couchbase_res[3])
    databases_total_dict = {index: name for index,
                            name in zip(eff_total_consumption, databases)}
    databases_co2_dict = {index: name for index,
                          name in zip(eff_co2_emissions, databases1)}
    sorted_total = [databases_total_dict[i]
                    for i in sorted(databases_total_dict, key=lambda x: Decimal(x))]
    sorted_co2 = [databases_co2_dict[j]
                  for j in sorted(databases_co2_dict, key=lambda x: Decimal(x))]
    eff_res.append(sorted_total[0])
    eff_res.append(sorted_co2[0])
    miles = []
    miles.append(mysql_res[4])
    miles.append(postgresql_res[4])
    miles.append(mongodb_res[4])
    miles.append(couchbase_res[4])
    tv = []
    tv.append(mysql_res[5])
    tv.append(postgresql_res[5])
    tv.append(mongodb_res[5])
    tv.append(couchbase_res[5])
    miles.sort()
    tv.sort()
    eff_res.append(miles[0])
    eff_res.append(tv[0])
    return render_template('compare_result.html', mysql_cpu_consumption=mysql_res[0], mysql_ram_consumption=mysql_res[1], mysql_total_consumption=mysql_res[2],
                           mysql_co2_emissions=mysql_res[3], mysql_miles_equvivalence=mysql_res[
                               4], mysql_tv_equvivalence=mysql_res[5],
                           postgresql_cpu_consumption=postgresql_res[0], postgresql_ram_consumption=postgresql_res[
                               1], postgresql_total_consumption=postgresql_res[2],
                           postgresql_co2_emissions=postgresql_res[3], postgresql_miles_equvivalence=postgresql_res[
                               4], postgresql_tv_equvivalence=postgresql_res[5],
                           mongodb_cpu_consumption=mongodb_res[0], mongodb_ram_consumption=mongodb_res[1], mongodb_total_consumption=mongodb_res[
                               2], mongodb_co2_emissions=mongodb_res[3], mongodb_miles_equvivalence=mongodb_res[4], mongodb_tv_equvivalence=mongodb_res[5],
                           couchbase_cpu_consumption=couchbase_res[0], couchbase_ram_consumption=couchbase_res[1], couchbase_total_consumption=couchbase_res[
                               2], couchbase_co2_emissions=couchbase_res[3], couchbase_miles_equvivalence=couchbase_res[4], couchbase_tv_equvivalence=couchbase_res[5],
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
        res = execute_mysql_query(query, 'root', password, db_name)
    else:
        db_name = request.form['db_name']
        res = execute_mongodb_query(query, db_name)

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


def execute_mysql_query(query, db_user, db_password, db_name):
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
        # print(result_set)
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


def execute_postgreSQL_query(postgresql_query, postgresql_user, postgresql_password, postgresql_db_name):
    obj = Tracker()
    # Tracker object starts to calculate the cpu,ram consumptions
    obj.start()
    res = []
    connection = psycopg2.connect(
        host='localhost', database=postgresql_db_name, user=postgresql_user, password=postgresql_password)
    cursor = connection.cursor()
    cursor.execute(postgresql_query)
    connection.commit()
    cursor.close()
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


def execute_couchbase_query(couchbase_query, couchbase_username, couchbase_password, couchbase_bucket_name):
    obj = Tracker()
    # Tracker object starts to calculate the cpu,ram consumptions
    obj.start()
    res = []
    auth = PasswordAuthenticator(couchbase_username, couchbase_password)
    cluster = Cluster.connect('couchbase://localhost', ClusterOptions(auth))

    # get a reference to our bucket
    cb = cluster.bucket(couchbase_bucket_name)

    # get a reference to the default collection
    cb_coll = cb.default_collection()
    query_res = cluster.query(couchbase_query)
    # for row in query_res:
    #     print(f'Found row: {row}')
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


def execute_mongodb_query(query, db_name):
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
        # split_quer_doc = query_doc.split(',')
        # arg_dict = []
        # for q in split_quer_doc:
        #     arg_dict.append(eval(q))
        arg_dict = eval(query_doc)
        result = collection.insert_one(arg_dict)
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
