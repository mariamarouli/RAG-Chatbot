import streamlit as st
import requests

# Function to call the FastAPI backend
def get_chat_response(username, question):
    response = requests.post("http://zentao-fastapi:8020/zentao-bot/ask", json={"username": username, "question": question})
    if response.status_code == 200:
        return response.json().get("text", "No response from API")
    else:
        return f"Error: {response.status_code}"


# Initialize session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask a question"}
    ]

# User input fields
username = st.text_input("Username:", "")
question = st.chat_input("Your question:")

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Handle new question
if question and username:
        # Append user message to chat history
    st.session_state.messages.append({"role": "user", "content": f"{username}: {question}"})
        
        # Display the user's message
    with st.chat_message("user"):
        st.write(f"{username}: {question}")
        
        # Fetch the chatbot response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_chat_response(username, question)
            
            # Display the chatbot response
        st.write(username)
        st.write(response)
            
            # Append the chatbot response to the chat history
        st.session_state.messages.append({"role": "assistant", "content": response})