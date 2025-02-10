import streamlit as st
import requests
import json
import os
import re

# Fixed Groq API Key
GROQ_API_KEY = "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"

# File to store chat histories
CHAT_HISTORY_FILE = "chat_history.json"
MIN_JSON_FILE = "min.json"  # File containing preloaded data for the AI
USER_DATA_FILE = "user_data.json"  # File to store user credentials

# Load chat history from file if it exists
def load_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, "r") as f:
                content = f.read()
                if not content.strip():
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            st.error("Chat history file is corrupted. Resetting to default.")
            return {}
    return {}

# Save chat history to file
def save_chat_history(chat_history):
    with open(CHAT_HISTORY_FILE, "w") as f:
        json.dump(chat_history, f)

# Delete chat history file
def delete_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        os.remove(CHAT_HISTORY_FILE)

# Load preloaded data from min.json
def load_min_json():
    if os.path.exists(MIN_JSON_FILE):
        try:
            with open(MIN_JSON_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error("Preloaded data file is corrupted. Using default content.")
            return {"content": "No preloaded data available."}
    return {"content": "No preloaded data available."}

# Load user data (credentials) from file
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error("User data file is corrupted. Resetting to default.")
            return {}
    return {}

# Save user data (credentials) to file
def save_user_data(user_data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f)

# Post-process the response to remove <think> tags and filter out invalid characters
def clean_response(response_text):
    # Remove <think> tags
    response_text = response_text.replace("<think>", "").replace("</think>", "")
    
    # Remove invalid or unsupported Unicode characters
    response_text = re.sub(r'[^\x00-\x7F]+', '', response_text)  # Remove non-ASCII characters
    return response_text

# Logout Functionality
def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.chats = {}
    delete_chat_history()
    st.rerun()

# Main Chat Application
def main_app():
    # Add Bootstrap Navigation Bar for Logged-In Users
    st.markdown("""
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">Jom Besut ChatBox</a>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="#" onclick="document.getElementById('logout').click()">Logout</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
    """, unsafe_allow_html=True)

    # Sidebar: Display logged-in user's name
    st.sidebar.title(f"Logged in as: {st.session_state.username}")
    if st.sidebar.button("Logout", key="logout"):
        logout()

    # Show title and description.
    st.title("💬 Jom Besut ChatBox")
    st.write(
        """
        Welcome to the Jom Besut Bot!  
        This app uses an advanced language model to generate responses in real-time.  
        You can create and switch between multiple conversations!
        """
    )

    # Initialize session state for managing multiple chats
    if "chats" not in st.session_state:
        st.session_state.chats = load_chat_history()  # Load chat history from file

    # Ensure there's at least one chat available
    if not st.session_state.chats:
        st.session_state.chats["Conversation 1"] = []  # Create a default chat if none exist

    if "current_chat" not in st.session_state:
        st.session_state.current_chat = next(iter(st.session_state.chats), "Conversation 1")  # Default active chat

    # Sidebar: Dropdown to select or create a new chat
    chat_options = list(st.session_state.chats.keys())
    selected_chat = st.sidebar.selectbox("Select Conversation", chat_options)
    new_chat_name = st.sidebar.text_input("Create New Conversation", placeholder="Enter conversation name")

    if st.sidebar.button("Add Conversation"):
        if new_chat_name.strip() and new_chat_name not in st.session_state.chats:
            st.session_state.chats[new_chat_name] = []  # Create a new chat
            st.session_state.current_chat = new_chat_name  # Switch to the new chat
            save_chat_history(st.session_state.chats)  # Save updated chat history
            st.rerun()  # Refresh the app to update the dropdown

    # Set the current chat based on the selected chat
    if selected_chat != st.session_state.current_chat:
        st.session_state.current_chat = selected_chat

    # Ensure the current chat exists in the chats dictionary
    if st.session_state.current_chat not in st.session_state.chats:
        st.session_state.current_chat = next(iter(st.session_state.chats), "Conversation 1")  # Fallback to default chat

    # Display the existing chat messages in a styled format.
    for message in st.session_state.chats[st.session_state.current_chat]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a chat input field to allow the user to enter a message.
    if prompt := st.chat_input("Ask me anything..."):
        # Store and display the current prompt.
        st.session_state.chats[st.session_state.current_chat].append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):  # User avatar
            st.markdown(prompt)

        # Prepare the request payload for Groq API.
        apiUrl = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        # Load preloaded data from min.json
        min_data = load_min_json()
        system_content = min_data.get("content", "No preloaded data available.")

        # Check if the user's prompt relates to Jom Besut (case-insensitive)
        if "jom besut" in prompt.lower():
            system_message = {"role": "system", "content": system_content}
        else:
            system_message = None

        # Construct the messages list
        messages = []
        if system_message:
            messages.append(system_message)  # Include preloaded data only if relevant

        # Detect if the user is speaking Malay
        if any(word in prompt.lower() for word in ["selamat", "terima kasih", "jom", "besut", "malaysia"]):
            system_message_malay = {"role": "system", "content": "Please respond in Malay."}
            messages.append(system_message_malay)

        messages.extend(
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.chats[st.session_state.current_chat]
        )

        data = {
            "model": "deepseek-r1-distill-llama-70b",  # Replace with the Groq model you want to use
            "messages": messages,
            "stream": True,
        }

        # Send the request to Groq API and handle streaming response.
        try:
            # Accumulate the full response text.
            response_text = ""
            with requests.post(apiUrl, headers=headers, json=data, stream=True) as response:
                response.raise_for_status()  # Raise an exception for HTTP errors
                if response.status_code != 200:
                    st.error(f"API returned status code {response.status_code}")
                    st.write(response.text)  # Display raw response for debugging
                    raise Exception("Invalid response from API")
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        if line.startswith("data: "):
                            line = line[6:]  # Remove "data: " prefix
                            if line.strip() == "[DONE]":
                                continue
                            try:
                                chunk = json.loads(line)
                                delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                response_text += delta
                            except json.JSONDecodeError:
                                st.error("Failed to decode JSON from API response.")
                                st.write(f"Raw line: {line}")
                                continue  # Skip invalid JSON lines

            # Clean the response text
            response_text = clean_response(response_text)

            # Display the assistant's response after accumulating all chunks.
            if response_text.strip():  # Only display non-empty responses
                with st.chat_message("assistant", avatar="🤖"):  # Assistant avatar
                    st.markdown(response_text)
                # Append the assistant's response to the current chat history.
                st.session_state.chats[st.session_state.current_chat].append({"role": "assistant", "content": response_text})
                save_chat_history(st.session_state.chats)  # Save updated chat history
            else:
                st.warning("The assistant did not provide a response.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")