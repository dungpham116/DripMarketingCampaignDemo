# Email Writing Agent
from crewai import Agent, Task, Crew, Process, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.knowledge.source.csv_knowledge_source import CSVKnowledgeSource
import yaml
import os
from dotenv import load_dotenv
load_dotenv('example.env')
# Knowledge base
FAQ = './a.csv' # Path to FAQ csv file
message_history = './b.csv' # Path to message-reply history
csv_source = CSVKnowledgeSource(
    file_paths = [FAQ, message_history]
)
llm = LLM(model="gpt-4o-mini", temperature=0)

agents_config_path = 'config/agents.yaml'
tasks_config_path = 'config/tasks.yaml'

with open('config/agents.yaml', 'r') as file:
    agents_config = yaml.safe_load(file)

with open('config/tasks.yaml', 'r') as file:
    tasks_config = yaml.safe_load(file)


# Create an agent with the knowledge store
writer_agent = Agent(
    role = agents_config['writer_agent']['role'],
    goal = agents_config['writer_agent']['goal'],
    backstory = agents_config['writer_agent']['backstory'],
    verbose=True,
    allow_delegation=False,
    llm=llm,
)
write_email_task = Task(
    description = tasks_config['write_email_task']['description'],
    expected_output = tasks_config['write_email_task']['expected_output'],
    agent=writer_agent,
)

email_writing_agent = Crew(
    agents=[writer_agent],
    tasks=[write_email_task],
    verbose=True,
    process=Process.sequential,
    knowledge_sources=[csv_source],
    # Enable knowledge by adding the sources here. You can also add more sources to the sources list.
)