import streamlit as st
import requests
import json
import os

# Fixed Groq API Key
GROQ_API_KEY = "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"

# File to store chat histories
CHAT_HISTORY_FILE = "chat_history.json"
MIN_JSON_FILE = "min.json"  # File containing preloaded data for the AI

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
            return {"content": "Tiada data pra-muatkan tersedia."}
    return {"content": "Tiada data pra-muatkan tersedia."}

# Show title and description.
st.title("💬 Jom Besut ChatBox")
st.write(
    """
    Selamat datang ke Jom Besut Bot!  
    Aplikasi ini menggunakan model bahasa canggih untuk menjana respons secara masa nyata.  
    Anda boleh mencipta dan bertukar antara beberapa perbualan!
    """
)

# Initialize session state for managing multiple chats
if "chats" not in st.session_state:
    st.session_state.chats = load_chat_history()  # Load chat history from file

# Ensure there's at least one chat available
if not st.session_state.chats:
    st.session_state.chats["Perbualan 1"] = []  # Create a default chat if none exist

if "current_chat" not in st.session_state:
    st.session_state.current_chat = next(iter(st.session_state.chats), "Perbualan 1")  # Default active chat

# Sidebar: Dropdown to select or create a new chat
chat_options = list(st.session_state.chats.keys())
selected_chat = st.sidebar.selectbox("Pilih Perbualan", chat_options)
new_chat_name = st.sidebar.text_input("Cipta Perbualan Baru", placeholder="Masukkan nama perbualan")

if st.sidebar.button("Tambah Perbualan"):
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
    st.session_state.current_chat = next(iter(st.session_state.chats), "Perbualan 1")  # Fallback to default chat

# Display the existing chat messages in a styled format.
for message in st.session_state.chats[st.session_state.current_chat]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Create a chat input field to allow the user to enter a message.
if prompt := st.chat_input("Tanya saya apa-apa..."):
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
    system_content = min_data.get("content", "Tiada data pra-muatkan tersedia.")

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
        system_message_malay = {"role": "system", "content": "Sila beri jawapan dalam Bahasa Melayu."}
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

# Add a "Delete All Chats" button in the sidebar
if st.sidebar.button("Padam Semua Perbualan"):
    # Use SweetAlert for confirmation before deleting
    st.components.v1.html("""
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <script>
    Swal.fire({
        title: 'Adakah anda pasti?',
        text: "Ini akan memadam semua perbualan secara kekal!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Ya, padamkan!'
    }).then((result) => {
        if (result.isConfirmed) {
            // Trigger Python function to delete chats
            fetch('/delete_all_chats', { method: 'POST' })
                .then(() => {
                    Swal.fire('Dipadam!', 'Semua perbualan telah dipadam.', 'success');
                    location.reload(); // Refresh the page
                });
        }
    });
    </script>
    """, height=0)

# Handle the deletion of all chats
if st.session_state.get("delete_all_chats"):
    # Clear all chats
    st.session_state.chats = {}
    delete_chat_history()
    st.session_state.current_chat = "Perbualan 1"
    st.session_state.pop("delete_all_chats")  # Reset the flag
    st.rerun()  # Refresh the app

# Button to trigger deletion in session state
if st.sidebar.button("Sahkan Padam Semua Perbualan (Debug)"):
    st.session_state["delete_all_chats"] = True