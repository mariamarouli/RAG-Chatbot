import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_core.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    FewShotPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate
)

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
database_schema = ""

mysql_uri = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database_schema}"

db = SQLDatabase.from_uri(mysql_uri, include_tables=['zt_bug', 'zt_task', 'zt_product', 'zt_project'])
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
                        

examples = [
    {
        "input": "List some projects and the tasks they contain.",
        "sql": """SELECT p.name AS poject_name, GROUP_CONCAT(DISTINCT t.name SEPARATOR ', ') AS task_names
                  FROM zt_project p
                  JOIN zt_task t ON t.project = p.project
                  GROUP BY p.name
                  LIMIT 10;
                """
    },

    {
        "input": "List some tasks and the projects they refer to.",
        "sql": """SELECT t.name AS task_name, GROUP_CONCAT(DISTINCT p.name SEPARATOR ', ') AS project_names
                  FROM zt_task t
                  JOIN zt_project p ON t.project = p.project
                  GROUP BY t.name
                  LIMIT 10;
                """
    },

    {
        "input": "How many days did the ΕΞΟΙΚΟΝΟΜΩ Γ ΚΥΚΛΟΣ 2 project last?",
        "sql": """SELECT DATEDIFF(realEnd, begin) FROM zt_project 
                  WHERE  name="ΕΞΟΙΚΟΝΟΜΩ Γ ΚΥΚΛΟΣ 2"
                """
    },

    {
        "input": "What is the date that the ΕΞΟΙΚΟΝΟΜΩ Γ ΚΥΚΛΟΣ 2 project closed and by whom?",
        "sql": """SELECT closedDate, closedBy FROM zt_project 
                  WHERE  name="ΕΞΟΙΚΟΝΟΜΩ Γ ΚΥΚΛΟΣ 2"
                """
    },

    {
        "input": "How many bugs per project were assigned to karatzioli? Display also the name of the projects.",
        "sql": """SELECT 
                  p.name AS project_name,
                  COUNT(*) AS bug_count,
                  FROM zt_bug b
                  JOIN 
                  zt_project p ON b.project = p.project
                  WHERE b.assignedTo = 'e.karatzioli'
                  GROUP BY p.name;
                """
    },

    {
        "input": "Display the number of products that are not closed along with their names.",
        "sql": """SELECT 
                  COUNT(*) AS total_normal_products,
                  GROUP_CONCAT(name SEPARATOR ', ') AS product_names
                  FROM zt_product
                  WHERE status = "normal";
                """
    },

    {
        "input": "How many projects are not closed and what are their names?",
        "sql": """SELECT COUNT(*) AS total_doing_projects,
                  GROUP_CONCAT(name SEPERATOR ', ') AS project_names
                  FROM zt_project 
                  WHERE status='doing'
               """
    },

    {
        "input": "Which tasks are completed?",
        "sql": "SELECT name FROM zt_task WHERE status='done'"
    },

    {
        "input": "Which products are not completed?",
        "sql": "SELECT name FROM zt_product WHERE status='normal'"
    },

    {
        "input": "How many bugs are resolved? Provide also their names.",
        "sql": """SELECT COUNT(*) AS total_bugs, 
                  GROUP_CONCAT(title SEPARATOR ', ') AS bug_titles
                  FROM zt_bug 
                  WHERE status='resolved'
               """
    }
]

system_prefix = """You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run, 
then look at the results of the query and return the answer. 
Unless the user specifies a specific number of examples they wish to obtain,
always limit your query to at most {top_k} results.
You can render the results by a relevant column to return the most interesting examples in the database.
Never query for all the columns from a specific table, only ask for the relevant columns given the question.
You have access to tools g=for interacting with the database. Only use the given tools.
Only use the information returned by the tools to construct your final answer.
You MUST double check your query before executing it. 
If you get an error while executing a query, rewrite the query and try again.

Use the following context to create the SQL query. 
Context:
The tables zt_bug, zt_task, zt_project are linked by the column project. 
So you need to use this column for generating sql queries that involve two of the former tables. 
Do not use the column id in zt_project table as it is just a primary key and unable to connect the tables.
The zt_project table contains the columns begin, end, realBegun, realEnd. When you want to compute 
date differences use either the columns realBegan and realEnd or the realEnd and begin columns
or realBegan and end columns or begin and end columns depending on which columns contain a date. 
If there are multiple entries in the zt_project table for the same project, 
use the most recent end and begin dates to compute date differences.

The zt_bug table's column status takes the following values: active, resolved, closed. 
If a user asks "how many bugs are completed?", use the status value closed to query the zt_bug table.

The column status of the zt_product table takes the following values: normal and closed.
If a user asks "which product is completed?", use the status value closed to query the zt_product table.

The status column of the zt_project table takes the following values: doing, closed, suspended, wait.
If a user asks "which projects are not closed yet?", use the status value doing to query the zt_project table.
If a user asks "which teams are behind the ehealthpass project?", use the column team that can be found in the zt_project table
for all the projects named ehealthpass. Do this for any project that the user may ask.

The status column of the zt_task table takes the following values: wait, doing, done, pause, cancel, closed.
If a user asks "which tasks are currently completed?", use the status value done to query the zt_task table.

The assignedTo column of the zt_bug table contains the following values: 
a.karabatea, a.papastergiou, closed, d.kazepidou, d.patelis, d.siotas, e.karatzioli,
e.sarafidou, f.gonidis, i.kakoulidis, k.karkaletsis, k.papadopoulou, karkaletsis,
m.kratouni, n.malamas, n.mpampamis, p.sarakinou, t.meresescu, t.tsouskos, v.georgakoudi.
A user will always ask with just the surname - e.g. in 't.tsouskos' the surname is 'tsouskos',
So you must make the required transformations and query the table with the full name - i.e. 't.tsouskos'. 

If a user input contains the word karkaletsis then perform two times the sql query.
One for the word karkaletsis and the other for the word k.karkaletsis (as they are the same).
Finally aggregate the results and display the final answer.

If a subquery returns more than one row, use the IN statement when forming the final query.
For example:
    SELECT COUNT(*) FROM zt_bug WHERE project IN (
        SELECT project FROM zt_project WHERE name='ehealthpass')

If the user question requires generating more than 1 sql query, then generate the queries and
execute one at a time. Finally, concatenate the results and display them.

Do not make any DML satements(INSERT, UPDATE, DELETE, DROP etc.) to the database.

If the question does not seem related to the database, just return "I don't know" as the answer.

Here are some examples with user inputs and the corresponding SQL queries: """


few_shot_prompt = FewShotPromptTemplate(
    example_prompt=PromptTemplate.from_template(
        "User input: {input}\nSQL query: {sql}"
    ),
    examples=examples,
    input_variables=["input", "dialect", "top_k"],
    prefix = system_prefix,
    suffix=""
)


final_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate(prompt=few_shot_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ]
)


agent_executor = create_sql_agent(
    llm=llm,
    db=db,
    prompt=final_prompt,
    verbose=True,
    agent_type="openai-tools"
)
