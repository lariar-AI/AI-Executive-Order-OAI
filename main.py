import sys
import os

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

import time


from openai import OpenAI
client = OpenAI()


#--------------------------------------
# #Creating a global thread object
#--------------------------------------
chat_thread = client.beta.threads.create()

#--------------------------------------
#Gradio callback after user enters text
#--------------------------------------
def slow_echo(usr_message, history):
  print(f"[Debug] -> User query is [{usr_message}]\n")

  #--create a message based on user's query
  msg = client.beta.threads.messages.create(
    thread_id=chat_thread.id,
    role="user",
    content=usr_message
  )
  print(f"[Debug] -> Sent message to assistant ...\n")  

  #--run the query on the assistant's thread
  run = client.beta.threads.runs.create(
    thread_id=chat_thread.id,
    assistant_id="asst_rKR4Ere5pU3Wcxh0TCE3imgk",
    instructions="Please be polite when you answer the queries."
  )

  #--wait for the completion and post it back on the chat messages
  while run.status != 'completed' and run.status != 'failed' :
    print(f"Waiting for run to complete. Current status is {run.status}\n")
    run = client.beta.threads.runs.retrieve(
            thread_id=chat_thread.id,
            run_id=run.id
    )
    time.sleep(1)

  #--store the current run to match it with the right response from the thread
  current_run = run.id

  messages = client.beta.threads.messages.list(
    thread_id=chat_thread.id
  )

  #--- look for the specific response to a run_id
  #--- have requested this as an enhancement to openai
  #--- https://community.openai.com/t/assistant-api-sdk-enhancement-get-message-by-run-id/484468
  for message in messages.data:
    if message.role == 'assistant' and message.run_id == current_run:
        response = message.content[0].text.value
        yield response

"""
demo = gr.ChatInterface(slow_echo,
                        title="AI Math Tutor",
                        description="AI Math Tutor is a virtual learning assistant that provides personalized math instruction, explanations, and practice problems to help you improve your math skills.",
                        theme="soft",
                        examples=["What is the square root of 256", "Explain BODMAS rule?", "25th Fibonacci number?"],
                        retry_btn=None,
                        undo_btn=None,
                        clear_btn=None).queue()

if __name__ == "__main__":
    demo.launch()
"""       




### Streamlit

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
        response = slow_echo(prompt,st_callback)
        st.write(response)

if st.button("Clear Chat"):
  st.session_state.messages = []