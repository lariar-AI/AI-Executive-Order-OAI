import sys
import os
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.callbacks import StreamlitCallbackHandler
from langchain.agents import AgentType, initialize_agent, load_tools
from langchain.agents import Tool, tool
import promptlayer  # Don't forget this 🍰
from langchain.callbacks import PromptLayerCallbackHandler
import streamlit as st
from langchain.memory import StreamlitChatMessageHistory
from load_documents import vectordb
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

openai_api_key = os.getenv('OPENAI_API_KEY')
promptlayer_api_key = os.getenv('PROMPTLAYER_API_KEY')


# Create summary prompt
sum_prompt = """
Summarize the following content, paying close attention to the details that may answer this user's question. 
---
Question: {question}
---
Context: {context}
---
Summary: """

SUMMARY_PROMPT = PromptTemplate(input_variables=["question","context"], template=sum_prompt)

# Create a summarizer LLM, chain using ChatOpenAI
llm = ChatOpenAI(
    temperature=0, 
    model_name="gpt-4",
    callbacks=[PromptLayerCallbackHandler(pl_tags=["research-agent","summarize_docs"])]
)

doc_summary = ConversationalRetrievalChain.from_llm(
    llm,
    vectordb.as_retriever(),
    condense_question_prompt=SUMMARY_PROMPT,
    chain_type="stuff"
)

# Create the agent LLM using ChatOpenAI
agentllm = ChatOpenAI(
   temperature=0, 
   model='gpt-4', 
   streaming=True,
   callbacks=[PromptLayerCallbackHandler(pl_tags=["research-agent","top-level"])]
)

# Create tool for accessing the summary LLM
@tool
def intermediate_steps(query: str) -> str:
    """Searches the AI Executive Order for a relevant answer to the user's question."""
    return doc_summary.run({"question": prompt, "chat_history": chat_history})

# Load tools
tools = [intermediate_steps]

"""
tools = [
    Tool(
        name="Intermediate Answer",
        func=intermediate_steps,
        description="useful for when you need to ask with search",
    )
        ]
"""

# Initialize agent with tools, agentllm, and memory
msgs = StreamlitChatMessageHistory(key="chat_history")
memory = ConversationBufferMemory(memory_key="history", chat_memory=msgs)

agent = initialize_agent(
    tools, 
    agentllm, 
    agent="chat-zero-shot-react-description", # AgentType.SELF_ASK_WITH_SEARCH, # 
    memory=memory,
    handle_parsing_errors=True
)  

# Define agent instructions
instructions = """
System Prompt: You are a Consulting Services AI assistant who has access to the new Executive Order on AI that is a topic of interest to the user. You will use available tools to search the text of the Executive Order to help answer questions. 

Follow these rules:
- Always use a tool. 
- It is OK to make multiple calls to this tool. 
- Break up complex questions into separate simple searches. 
- Always cite your sources.
----
User Prompt: "
"""

# Set the title of the Streamlit application
st.title('AI Executive Order Chatbot')
# Display a brief description of the application
st.text('Ask questions related to the AI Executive Order')

# Initialize an empty list to store chat history
chat_history = []

# Check if the session state already has a 'messages' key, if not, initialize it
if "messages" not in st.session_state:
  st.session_state.messages = []



# Display previous chat messages when the application is rerun
#for message in st.session_state.messages:
#  with st.chat_message(message["role"]):
#    st.markdown(message["content"])

# Initialize a memory buffer to store the chat history
memory = ConversationBufferMemory(memory_key="chat_history")



if prompt := st.chat_input('Ask a question about the AI Executive Order'):
    st.chat_message("user").write(prompt)
    with st.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())
        response = agent.run(instructions+prompt, callbacks=[st_callback])
        st.write(response)

if st.button("Clear Chat"):
  st.session_state.messages = []