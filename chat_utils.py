import streamlit as st
import requests
import json
import os
import re

GROQ_API_KEY = "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"
CHAT_HISTORY_FILE = "chat_history.json"
MIN_JSON_FILE = "min.json"
USER_DATA_FILE = "user_data.json"

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

def save_chat_history(chat_history):
    with open(CHAT_HISTORY_FILE, "w") as f:
        json.dump(chat_history, f)

def delete_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        os.remove(CHAT_HISTORY_FILE)

def load_min_json():
    if os.path.exists(MIN_JSON_FILE):
        try:
            with open(MIN_JSON_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error("Preloaded data file is corrupted. Using default content.")
            return {"content": "No preloaded data available."}
    return {"content": "No preloaded data available."}

def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error("User data file is corrupted. Resetting to default.")
            return {}
    return {}

def save_user_data(user_data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f)

def clean_response(response_text):
    response_text = response_text.replace("", "").replace("", "")
    response_text = re.sub(r'[^\x00-\x7F]+', '', response_text)
    return response_text

def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.chats = {}
    delete_chat_history()
    st.rerun()

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
        padding: 10px 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        max-width: 80%;
        align-self: flex-end;
    }
    .assistant-message {
        background-color: #f1f1f1;
        color: black;
        padding: 10px 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        max-width: 80%;
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

def streamlit_app():
    add_custom_css()
    st.sidebar.title(f"{st.session_state.username}")
    if st.sidebar.button("Logout"):
        logout()
    st.write("""
    Welcome to the Jom Besut Bot!  
    This app uses an advanced language model to generate responses in real-time.  
    You can create and switch between multiple conversations!
    """)
    if "chats" not in st.session_state:
        st.session_state.chats = load_chat_history()
    if not st.session_state.chats:
        st.session_state.chats["Conversation 1"] = []
    if "current_chat" not in st.session_state:
        st.session_state.current_chat = next(iter(st.session_state.chats), "Conversation 1")
    chat_options = list(st.session_state.chats.keys())
    selected_chat = st.sidebar.selectbox("Select Conversation", chat_options)
    new_chat_name = st.sidebar.text_input("Create New Conversation", placeholder="Enter conversation name")
    if st.sidebar.button("Add Conversation"):
        if new_chat_name.strip() and new_chat_name not in st.session_state.chats:
            st.session_state.chats[new_chat_name] = []
            st.session_state.current_chat = new_chat_name
            save_chat_history(st.session_state.chats)
            st.rerun()
    if selected_chat != st.session_state.current_chat:
        st.session_state.current_chat = selected_chat
    if st.session_state.current_chat not in st.session_state.chats:
        st.session_state.current_chat = next(iter(st.session_state.chats), "Conversation 1")
    for message in st.session_state.chats[st.session_state.current_chat]:
        if message["role"] == "user":
            st.markdown(f"""
{message["content"]}
U
            """, unsafe_allow_html=True)
        elif message["role"] == "assistant":
            st.markdown(f"""
AI
{message["content"]}
            """, unsafe_allow_html=True)
    if prompt := st.chat_input("Ask me anything..."):
        st.session_state.chats[st.session_state.current_chat].append({"role": "user", "content": prompt})
        st.markdown(f"""
{prompt}
U
        """, unsafe_allow_html=True)
        apiUrl = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        min_data = load_min_json()
        system_content = min_data.get("content", "No preloaded data available.")
        if "jom besut" in prompt.lower():
            system_message = {"role": "system", "content": system_content}
        else:
            system_message = None
        messages = []
        if system_message:
            messages.append(system_message)
        if any(word in prompt.lower() for word in ["selamat", "terima kasih", "jom", "besut", "malaysia"]):
            system_message_malay = {"role": "system", "content": "Please respond in Malay."}
            messages.append(system_message_malay)
        messages.extend(
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.chats[st.session_state.current_chat]
        )
        data = {
            "model": "deepseek-r1-distill-llama-70b",
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
            response_text = clean_response(response_text)
            if response_text.strip():
                st.markdown(f"""
AI
{response_text}
                """, unsafe_allow_html=True)
                st.session_state.chats[st.session_state.current_chat].append({"role": "assistant", "content": response_text})
                save_chat_history(st.session_state.chats)
            else:
                st.warning("The assistant did not provide a response.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    streamlit_app()