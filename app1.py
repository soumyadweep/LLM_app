import streamlit as st
import random
import time
import asyncio
from functions import get_chat_history_as_json,get_chat_history_as_text

from workflow import askWeb
st.title("Text to Text and Image Chatbot")


# Streamed response emulator
def response_generator(userquery):
    response =  asyncio.run(askWeb(userquery))
    #for word in response.split():
        #yield word + " "
        #time.sleep(0.05)
    return response[1]

#Function to parse output to display in a attracting manner
def answer_parser(answer):
    ans1=answer.replace('{', '').replace('}', '')
    ans2= ans1.split(',')
    ans = '\n'.join(ans2) 
    return ans
# Function to parse and display response

def display_animal_details(response):
    try:
        animals = eval(response)
       # Convert string response to Python list (use cautiously, prefer json.loads for safety)
        for animal in animals:
            # Display the text details
            try:
                details = str(animal['Details'])  # Attempt to get 'Details'
                if isinstance(details, str):
                    st.write(answer_parser(details))
                else:
                    st.error("Invalid format for 'Details'")
            except KeyError:
                st.error("'Details' key is missing in the response.")

            # Display the image if the link is available
            try:
                link = animal['Link']  # Attempt to get 'Link'
                st.image(link, caption="Animal", use_container_width=False)
            except KeyError:
                st.markdown("No picture available for this animal.")
            #except Exception as e:
                #st.error(f"Error displaying image: {e}")

            st.divider()
    except Exception as e:
        #st.error(f"Error parsing or displaying response: {e}")
        st.write(response)



# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

## Display chat history in the sidebar
with st.sidebar:
    st.header("Chat History")
    if st.session_state.messages:
        # JSON download
        st.download_button(
            label="Download Chat History (JSON)",
            data=get_chat_history_as_json(),
            file_name="chat_history.json",
            mime="application/json",
        )
        # Text download
        st.download_button(
            label="Download Chat History (Text)",
            data=get_chat_history_as_text(),
            file_name="chat_history.txt",
            mime="text/plain",
        )
    else:
        st.write("No chat history to download.")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask your question here"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    #response = st.write_stream(response_generator())
    # Streamed response emulator

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        response=response_generator(prompt)
        if response:
            display_animal_details(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
