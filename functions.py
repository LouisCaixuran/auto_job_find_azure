import json
import os
from openai import AzureOpenAI as OpenAI
from dotenv import load_dotenv
from config import *
load_dotenv()

os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_VERSION"] = OPENAI_VERSION
os.environ["AZURE_OPENAI_ENDPOINT"] = OPENAI_BASE_URL
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Init OpenAI Client
client = OpenAI(azure_deployment=OPENAI_DEPLOYMENT,api_key=OPENAI_API_KEY, api_version=OPENAI_VERSION, azure_endpoint=OPENAI_BASE_URL)
assistant_instructions = """
    本助手将扮演一位求职者的角色，根据上传的pdf简历以及应聘工作的描述，来直接给HR写一个礼貌专业的求职新消息，要求能够用专业的语言结合简历中的经历和技能，并结合应聘工作的描述，来阐述自己的优势，尽最大可能打动招聘者。并且请您始终使用中文来进行消息的编写,开头是招聘负责人，结尾是真诚的，付尧全。这是一封完整的求职信，不要包含求职信内容以外的东西，例如“根据您上传的求职要求和个人简历，我来帮您起草一封求职邮件：”这一类的内容，以便于我直接自动化复制粘贴发送
"""
# Create or load assistant
def create_assistant(client):
  assistant_file_path = 'assistant.json'

  # If there is an assistant.json file already, then load that assistant
  if os.path.exists(assistant_file_path):
    with open(assistant_file_path, 'r') as file:
      assistant_data = json.load(file)
      assistant_id = assistant_data['assistant_id']
      print("Loaded existing assistant ID.")
  else:
    # If no assistant.json is present, create a new assistant using the below specifications

    # To change the knowledge document, modify the file name below to match your document
    # If you want to add multiple files, paste this function into ChatGPT and ask for it to add support for multiple files
    file = client.files.create(file=open("my_cover.pdf", "rb"),
                               purpose='assistants')

    assistant = client.beta.assistants.create(
        # Getting assistant prompt from "prompts.py" file, edit on left panel if you want to change the prompt
        instructions=assistant_instructions,
        model="gpt-35-turbo-16k",
        tools=[
            {
                "type": "retrieval"  # This adds the knowledge base as a tool
            },
        ],
        file_ids=[file.id])
    print("created assistant\n")
    # Create a new assistant.json file to load on future runs
    with open(assistant_file_path, 'w') as file:
      json.dump({'assistant_id': assistant.id}, file)
      print("Created a new assistant and saved the ID.")

    assistant_id = assistant.id

  return assistant_id
