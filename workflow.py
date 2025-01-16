from openai import OpenAI
import os
import time
import json
import nest_asyncio
from tqdm.auto import tqdm
from dotenv import load_dotenv
import asyncio
import sqlite3

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

tools=[
     {
        "type": "function",
        "function": {
            "name": "get_animal_details",
            "description": """Answer animal related questions""",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": """Mostly questions are related to animal details""",
                    }
                },
                "required": ["query"]
            }
        }
    }
  
]

def execute_sql_query(db_path, sql_query):
   conn = sqlite3.connect(db_path)
   cursor = conn.cursor()
   cursor.execute(sql_query)
   rows = cursor.fetchall()
   conn.close()
   return rows

def get_animal_details(query):
    # db_retrieved_results=perform_search(query, model, 'ComplianceData')
    # similardata=[]
    # for element in db_retrieved_results:
    #     similardata.append(element.payload)    
    prompt=f"""You are a human expert in understanding and generating sql query for a user question. You will be given a user question: 'query'.\\
     and the schema of the related table. The table contains information about animals.  
     
     Here is the database schema to further enhance your information to form the sql query.
    Database Schema: (
         Name: The name of the animal
         Age: The age of the animal
         Link: The link to image of the animal
         Colour: The colour of the animal
        )
         The table name is 'test'.
        Based on the above database schema create sql query for User question: {query}
         Remember:
         (1) Always create LIKE query in the WHERE clause to match strings

          Output the sql only,like :  "SELECT * FROM test WHERE Name LIKE '%dog%'"
 Don't put the 'sql' word infront of the output query.
"""
    response = client.chat.completions.create(
    model="gpt-4o-mini",#"gpt-3.5-turbo",
  # response_format={ "type": "json_object" },
    messages=[
    {"role": "system", "content": prompt},
    {"role": "user", "content": f"{query}"}
  ]
)   
    sql_query=response.choices[0].message.content
    #print(sql_query)
    try:
        db_path='llmapp.db'
        result = execute_sql_query(db_path, sql_query=str(sql_query))
        return str(result)
    except sqlite3.OperationalError as e:
        return f"OperationalError: {str(e)}"
    except sqlite3.IntegrityError as e:
        return f"IntegrityError: {str(e)}"
    except sqlite3.DatabaseError as e:
        return f"DatabaseError: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


assistant = client.beta.assistants.create(
  name="ARC AI",
  instructions="""You are a helpful AI agent. Give highly specific answers based on the information you're provided. Prefer to gather information with the tools provided to you rather than giving basic, generic answers.\n
                 """,
  tools=tools,
  model="gpt-4o-mini",#"gpt-4o",
)
thread = client.beta.threads.create()

async def agent(query):
    # query_type = classificationdata(query)
    message = client.beta.threads.messages.create(
      thread_id=thread.id,
      role="user",
      content=f"{query}"
    )
    run = client.beta.threads.runs.create_and_poll(
      thread_id=thread.id,
      assistant_id=assistant.id,
      instructions=f"""You are an expert in calling functions and answering user query. 
      Here is the database schema to further enhance your information to form the sql query.
    Database Schema: (
         Name: The name of the animal
         Age: The age of the animal
         Colour: The colour of the animal
         Link: The link to image of the animal
         
        )

        The retrieved data from tool calls will have data in the above said format. Return the answer in the following Format like this:
        Answer: [{{"Details": all the other details,'Link':the link"}}],
        dont output the worf Answer before the output."""
)
    required_actions = None
    while True:
        time.sleep(1)    
        run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
        #print(run_status)
        if run_status.status == 'completed':
            messages = client.beta.threads.messages.list(
                    thread_id=thread.id,limit=5
                )
        
                # Loop through messages and print content based on role
            # print(messages)
            for msg in messages.data:
                role = msg.role
                content = msg.content[0].text.value
                print(f"{role.capitalize()}: {content}")
            return required_actions,messages.data[0].content[0].text.value
        elif run_status.status == 'requires_action':
            print("Function Calling")
            required_actions = run_status.required_action.submit_tool_outputs.model_dump()
            #print(required_actions)
            tool_outputs = []
            import json
            for action in required_actions["tool_calls"]:
                # print(action)
                func_name = action['function']['name']
                arguments = json.loads(action['function']['arguments'])
                output = globals()[func_name](**arguments)
                #print('output:',output)
                tool_outputs.append({
                        "tool_call_id": action['id'],
                        "output": output
                    })
            #print('tool_outputs:',tool_outputs)        
            print("Submitting outputs back to the Assistant...")
            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs )
        else:
            #print(run_status.status)
            print("Waiting for the Assistant to process...")
            time.sleep(1)


async def askWeb(query):
    return await agent(query)
#answer= asyncio.run(askWeb("give details of dog"))
#print(f"Type:{type(answer)}")