import streamlit as st
import json



# Function to get chat history as JSON
def get_chat_history_as_json():
    return json.dumps(st.session_state.messages, indent=2)

# Function to get chat history as text
def get_chat_history_as_text():
    history_text = []
    for message in st.session_state.messages:
        role = "User" if message["role"] == "user" else "Assistant"
        content = message["content"]
        history_text.append(f"{role}: {content}")
    return "\n\n".join(history_text)