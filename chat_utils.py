import streamlit as st
import requests
import json
import os
import re

# Fixed Groq API Key
GROQ_API_KEY = "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"

# File paths
CHAT_HISTORY_FILE = "chat_history.json"
MIN_JSON_FILE = "min.json"  # File containing preloaded data for the AI
USER_DATA_FILE = "user_data.json"  # File to store user credentials
SESSION_STATE_FILE = "session_state.json"  # File to persist session state

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

# Load session state from file
def load_session_state():
    if os.path.exists(SESSION_STATE_FILE):
        try:
            with open(SESSION_STATE_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error("Session state file is corrupted. Resetting to default.")
            return {}
    return {}

# Save session state to file
def save_session_state(session_state):
    with open(SESSION_STATE_FILE, "w") as f:
        json.dump(session_state, f)

# Post-process the response to remove tags and filter out invalid characters
def clean_response(response_text):
    response_text = re.sub(r'[^\x00-\x7F]+', '', response_text)  # Remove non-ASCII characters
    return response_text

# Logout Functionality
def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.chats = {}
    delete_chat_history()
    if os.path.exists(SESSION_STATE_FILE):
        os.remove(SESSION_STATE_FILE)  # Clear persisted session state
    st.rerun()

# Custom CSS for chat styling
def add_custom_css():
    st.markdown("""
    <style>
    .chat-container {
        max-width: 800px;
        margin: auto;
        padding: 20px;
    }
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 15px 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        max-width: 90%;
        font-size: 18px;
        align-self: flex-end;
    }
    .assistant-message {
        background-color: #f1f1f1;
        color: black;
        padding: 15px 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        max-width: 90%;
        font-size: 18px;
        align-self: flex-start;
    }
    .stTextInput > div > div > input {
        border-radius: 10px;
        padding: 10px;
        font-size: 16px;
    }
    .chat-box {
        height: 600px;
        overflow-y: auto;
        border: 1px solid #ddd;
        padding: 10px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Analyze uploaded document using Groq API
def analyze_document(document_content):
    apiUrl = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    messages = [
        {"role": "system", "content": "Analyze the following document and provide a summary or key insights:"},
        {"role": "user", "content": document_content},
    ]
    data = {
        "model": "whisper-large-v3",  # Replace with the Groq model you want to use
        "messages": messages,
        "stream": True,
    }
    try:
        response_text = ""
        with requests.post(apiUrl, headers=headers, json=data, stream=True) as response:
            response.raise_for_status()
            if response.status_code != 200:
                st.error(f"API returned status code {response.status_code}")
                st.write(response.text)
                raise Exception("Invalid response from API")
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith("data: "):
                        line = line[6:]
                        if line.strip() == "[DONE]":
                            continue
                        try:
                            chunk = json.loads(line)
                            delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            response_text += delta
                        except json.JSONDecodeError:
                            st.error("Failed to decode JSON from API response.")
                            st.write(f"Raw line: {line}")
                            continue
        return clean_response(response_text)
    except Exception as e:
        st.error(f"An error occurred while analyzing the document: {str(e)}")
        return None

# Main Chat Application
def streamlit_app():
    # Add custom CSS
    add_custom_css()

    # Load session state from file if it exists
    if "logged_in" not in st.session_state:
        session_state = load_session_state()
        st.session_state.logged_in = session_state.get("logged_in", False)
        st.session_state.username = session_state.get("username", None)
        st.session_state.chats = session_state.get("chats", {})

    # If not logged in, redirect to login page
    if not st.session_state.logged_in:
        st.write("Please log in to continue.")
        return

    # Sidebar: Display logged-in user's name
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    if st.sidebar.button("Logout"):
        logout()

    # Add "Clear All Chats" button
    if st.sidebar.button("Clear All Chats"):
        st.session_state.chats = {}
        delete_chat_history()
        st.rerun()

    # Document Upload Section
    st.sidebar.header("Upload Document for Analysis")
    uploaded_file = st.sidebar.file_uploader("Choose a file", type=["txt", "pdf"])
    if uploaded_file is not None:
        st.sidebar.write("File uploaded successfully!")
        if st.sidebar.button("Analyze Document"):
            if uploaded_file.type == "text/plain":
                document_content = uploaded_file.read().decode("utf-8")
            elif uploaded_file.type == "application/pdf":
                from pypdf import PdfReader
                pdf_reader = PdfReader(uploaded_file)
                document_content = "\n".join(page.extract_text() for page in pdf_reader.pages)
            else:
                st.error("Unsupported file type. Please upload a .txt or .pdf file.")
                return

            st.sidebar.write("Analyzing document...")
            analysis_result = analyze_document(document_content)
            if analysis_result:
                st.sidebar.write("Analysis Complete:")
                st.sidebar.write(analysis_result)

    # Show title and description
    st.write("""
    Welcome to the Jom Besut Bot!  
    This app uses an advanced language model to generate responses in real-time.  
    You can create and switch between multiple conversations!
    """)

    # Initialize session state for managing multiple chats
    if "chats" not in st.session_state or not st.session_state.chats:
        st.session_state.chats = load_chat_history()  # Load chat history from file
    if not st.session_state.chats:
        st.session_state.chats["Conversation 1"] = []  # Create a default chat if none exist
    if "current_chat" not in st.session_state:
        st.session_state.current_chat = next(iter(st.session_state.chats), "Conversation 1")

    # Sidebar: Dropdown to select or create a new chat
    chat_options = list(st.session_state.chats.keys())
    selected_chat = st.sidebar.selectbox("Select Conversation", chat_options)
    new_chat_name = st.sidebar.text_input("Create New Conversation", placeholder="Enter conversation name")
    if st.sidebar.button("Add Conversation"):
        if new_chat_name.strip() and new_chat_name not in st.session_state.chats:
            st.session_state.chats[new_chat_name] = []
            st.session_state.current_chat = new_chat_name
            save_chat_history(st.session_state.chats)
            st.rerun()

    # Set the current chat based on the selected chat
    if selected_chat != st.session_state.current_chat:
        st.session_state.current_chat = selected_chat

    # Ensure the current chat exists in the chats dictionary
    if st.session_state.current_chat not in st.session_state.chats:
        st.session_state.current_chat = next(iter(st.session_state.chats), "Conversation 1")

    # Display the existing chat messages in a styled format.
    for message in st.session_state.chats[st.session_state.current_chat]:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
        elif message["role"] == "assistant":
            st.markdown(f'<div class="assistant-message">{message["content"]}</div>', unsafe_allow_html=True)

    # Create a chat input field to allow the user to enter a message.
    if prompt := st.chat_input("Ask me anything..."):
        # Store and display the current prompt.
        st.session_state.chats[st.session_state.current_chat].append({"role": "user", "content": prompt})
        st.markdown(f'<div class="user-message">{prompt}</div>', unsafe_allow_html=True)

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
                st.markdown(f'<div class="assistant-message">{response_text}</div>', unsafe_allow_html=True)

                # Append the assistant's response to the current chat history.
                st.session_state.chats[st.session_state.current_chat].append({"role": "assistant", "content": response_text})
                save_chat_history(st.session_state.chats)  # Save updated chat history
            else:
                st.warning("The assistant did not provide a response.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    # Persist session state to file
    session_state_to_save = {
        "logged_in": st.session_state.logged_in,
        "username": st.session_state.username,
        "chats": st.session_state.chats,
    }
    save_session_state(session_state_to_save)

# Run the app
if __name__ == "__main__":
    streamlit_app()