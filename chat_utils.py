import streamlit as st
import requests
import json
import os
import re
from pypdf import PdfReader

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
        "model": "deepseek-r1-distill-qwen-32b",  # Replace with the Groq model you want to use
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

# Post-process the response to remove tags and filter out invalid characters
def clean_response(response_text):
    response_text = re.sub(r'[^\x00-\x7F]+', '', response_text)  # Remove non-ASCII characters
    return response_text

# Main Chat Application
def streamlit_app():
    # Sidebar: Display logged-in user's name
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    if st.sidebar.button("Logout"):
        logout()

    # Show title and description
    st.write("""
    Welcome to the Jom Besut Bot!  
    This app uses an advanced language model to generate responses in real-time.  
    You can create and switch between multiple conversations!
    """)

    # Initialize session state for managing multiple chats
    if "chats" not in st.session_state:
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

    # Combined Input Area: Text Input + File Uploader
    col1, col2 = st.columns([4, 1])
    with col1:
        prompt = st.chat_input("Ask me anything...")
    with col2:
        uploaded_file = st.file_uploader("Upload", type=["txt", "pdf"], label_visibility="collapsed")

    # Handle Uploaded Document
    if uploaded_file is not None:
        if uploaded_file.type == "text/plain":
            document_content = uploaded_file.read().decode("utf-8")
        elif uploaded_file.type == "application/pdf":
            pdf_reader = PdfReader(uploaded_file)
            document_content = "\n".join(page.extract_text() for page in pdf_reader.pages)
        else:
            st.error("Unsupported file type. Please upload a .txt or .pdf file.")
            return

        st.write("Analyzing document...")
        analysis_result = analyze_document(document_content)
        if analysis_result:
            st.session_state.chats[st.session_state.current_chat].append({"role": "user", "content": "Uploaded Document"})
            st.session_state.chats[st.session_state.current_chat].append({"role": "assistant", "content": analysis_result})
            save_chat_history(st.session_state.chats)
            st.rerun()

    # Handle User Prompt
    if prompt:
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

            response_text = clean_response(response_text)

            if response_text.strip():
                st.markdown(f'<div class="assistant-message">{response_text}</div>', unsafe_allow_html=True)
                st.session_state.chats[st.session_state.current_chat].append({"role": "assistant", "content": response_text})
                save_chat_history(st.session_state.chats)
            else:
                st.warning("The assistant did not provide a response.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Run the app
if __name__ == "__main__":
    streamlit_app()