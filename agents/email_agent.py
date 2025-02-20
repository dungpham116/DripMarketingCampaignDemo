from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import SystemMessage
from langchain_openai import ChatOpenAI
from tools.email_tools import CategorizeEmailTool, EmailWriterTool
from config import Config
from typing import Any, Dict
from langchain.agents import AgentExecutor

class EmailAgent:
    def __init__(self):
        self.llm = self._initialize_llm()
        self.tools = [CategorizeEmailTool(), EmailWriterTool()]
        self.agent_executor = self._create_agent()  # Rename to agent_executor
    
    def __call__(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Make the class callable like AgentExecutor"""
        return self.agent_executor(inputs)
    
    @property
    def agent(self) -> AgentExecutor:
        """Direct access to the AgentExecutor instance"""
        return self.agent_executor

    def _initialize_llm(self):
        return ChatOpenAI(temperature=0, model="gpt-4o", api_key=Config.OPENAI_KEY)
    
    def _create_agent(self):
        system_message = SystemMessage(content=
                """
                You are an email inbox assistant of an Ron who is CEO of Hyred,
                Which provides HR-solutions to technical and non-technical organizations
                Ron have sent a cold email to some leads and you have provided a conversation history between info mation (Ron's email) and the lead

                Follow these steps while generating email reply:
                Step-1: First categorize the email based on given conversation history and get the category of email.
                Step-2: Check the sender of the last message and if the sender is NOT info mation then goto step-3.
                If the sender of last message is info mation then you don't need to construct a reply

                Step-3: Once you get the category, follow these conditions while constructing a reply email:
                1. If category is "Meeting_Ready_Lead" or "Power", you construct the reply email
                2. For all the other categories, DON'T construct a reply

                Your final response MUST BE in json with these keys:
                reply: Constructed email reply for positive email (leave it blank if no reply constructed or the last sender is rohan sawant)
                category: Category of given email based on email conversation history

                RESPONSE(Do not include any extra text, markdown, or formatting. Only return the JSON object.):
                """
                                       )
        memory = ConversationBufferWindowMemory(
            memory_key='memory',
            k=1,
            return_messages=True
        )
        return initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
            agent_kwargs={"system_message": system_message},
            memory=memory,
            handle_parsing_errors=True
        )