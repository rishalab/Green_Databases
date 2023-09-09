# Green Databases
**Team :**
1. K.Manasa - CS20B019
2. L.Hemasri Sai - CS20B020

**Description:** 



  
**Features:**
* Comparision of energy metrics among SQL and NOSQL query languages.
* Execution of a single query of either of the languages.
* Results displayed in the form of tables and real world equivalents.
* Real world equivalents include average miles travelled and average TV watch time.

**Note**
* The "query document" or "query object" should be written in JSON format.
* Implemented a portion of the query execution operations that are available in MongoDB. This subset includes the most commonly used operations. See mongo_operation.txt in docs folder.

**Technologies:**  
* Editor: vscode
* Language: python
* WebApp: Flask

**Instructions To Run:**  
1) Clone repo   
2) Run "setup.py" file to install necessary dependencies.
3) Run "stop_background_processes.py" file to stop all the currently running background processes.
4) Command to start the tool - python main_app.py  

# Tool Demo:
![ecodb](https://user-images.githubusercontent.com/84029615/233855298-259bc677-0ec3-4d6d-9415-b41b25d54037.png)

**Limitations**
 * Only supports MySQL, PostgreSQL, MongoDB and Couchbase databases.
 * Does not support more complex queries such as operations chaining. 
