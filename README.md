# EcoPyD
**Team :**
1. A.Pooja Sree - CS20B002
2. G.Namitha Reddy - CS20B011
3. K.Manasa - CS20B019
4. L.Hemasri Sai - CS20B020

**Description:** 

we introduce EcoPyD tool, designed to evaluate the energy consumption and carbon emissions associated with the execution of Python codes and databases, encompassing both SQL and NoSQL technologies. It comprises two components: EcoPy and EcoDB, where EcoPy calculates the metrics for Python files, and EcoDB computes the metrics for different databases, facilitating comparative analysis between MySQL and MongoDB databases.

The EcoPyD tool is particularly relevant in today's context, where the demand for computational power to query databases has significantly increased, leading to significant energy consumption and related costs.The tool's user-friendly interface, combined with its real-world equivalents, allows users to better comprehend the environmental impact of their database usage, ultimately leading to better-informed decisions that benefit both the environment and the business. Overall, EcoPyD is an essential tool that can contribute significantly to building a more sustainable and energy-efficient future.

  
**Features:**


**EcoPy**
* Calculates energy and carbon footprinting for python code
    - Energy consumption by CPU in KWh
    - Energy consumption by RAM in KWh
    - Total power consumption in KW
    - Carbon Footprint in Kg
* Calculates these four metrics of entire python file
* Also calculates for each and every function present in the python file
* Values of these metrics for a file and every function can be viewed in a table
* Energy and carbon footprint values can be compared between the functions using graphs

**EcoDB**
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
3) Command to start the tool - python main_app.py  

# Tool Demo:
**EcoPy**


![ecopy](https://user-images.githubusercontent.com/84029615/233855300-5f45e11f-adde-43fc-bbcc-c6b06fbdc73f.png)

**EcoDB**


![ecodb](https://user-images.githubusercontent.com/84029615/233855298-259bc677-0ec3-4d6d-9415-b41b25d54037.png)

**Limitations**
 * Only support MySQL and MongoDB databases
 * Does not support more complex queries such as operations chaining 
