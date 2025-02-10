import streamlit as st
import requests
import json
import os

# Fixed Groq API Key
GROQ_API_KEY = "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"

# File to store chat histories
CHAT_HISTORY_FILE = "chat_history.json"

# Load chat history from file if it exists
def load_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r") as f:
            return json.load(f)
    return {}

# Save chat history to file
def save_chat_history(chat_history):
    with open(CHAT_HISTORY_FILE, "w") as f:
        json.dump(chat_history, f)

# Delete chat history file
def delete_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        os.remove(CHAT_HISTORY_FILE)

# Show title and description.
st.title("💬 Chatbot")
st.write(
    """
    Welcome to the Jom Besut Chatbot!  
    This app uses Jom Besut ChatBox's advanced language models to generate responses in real-time.  
    You can create and switch between multiple chats!
    """
)

# Initialize session state for managing multiple chats
if "chats" not in st.session_state:
    st.session_state.chats = load_chat_history()  # Load chat history from file

# Ensure there's at least one chat available
if not st.session_state.chats:
    st.session_state.chats["Chat 1"] = []  # Create a default chat if none exist

if "current_chat" not in st.session_state:
    st.session_state.current_chat = next(iter(st.session_state.chats), "Chat 1")  # Default active chat

# Sidebar: Dropdown to select or create a new chat
chat_options = list(st.session_state.chats.keys())
selected_chat = st.sidebar.selectbox("Select Chat", chat_options)
new_chat_name = st.sidebar.text_input("Create New Chat", placeholder="Enter chat name")

if st.sidebar.button("Add Chat"):
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
    st.session_state.current_chat = next(iter(st.session_state.chats), "Chat 1")  # Fallback to default chat

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
    data = {
        "model": "llama-3.3-70b-versatile",  # Replace with the Groq model you want to use
        "messages": [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.chats[st.session_state.current_chat]
        ],
        "stream": True,
    }

    # Send the request to Groq API and handle streaming response.
    try:
        # Accumulate the full response text.
        response_text = ""
        with requests.post(apiUrl, headers=headers, json=data, stream=True) as response:
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Debugging: Log the raw response for inspection.
            if response.status_code != 200:
                st.error(f"API returned status code {response.status_code}")
                st.write(response.text)  # Display raw response for debugging
                raise Exception("Invalid response from API")

            for line in response.iter_lines(decode_unicode=True):
                if line:
                    # Parse the JSON object from the SSE line.
                    if line.startswith("data: "):
                        line = line[6:]  # Remove "data: " prefix

                        # Skip non-JSON lines like "[DONE]"
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
if st.sidebar.button("Delete All Chats"):
    # Use SweetAlert for confirmation before deleting
    st.components.v1.html("""
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <script>
    Swal.fire({
        title: 'Are you sure?',
        text: "This will delete all chats permanently!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Yes, delete it!'
    }).then((result) => {
        if (result.isConfirmed) {
            // Trigger Python function to delete chats
            fetch('/delete_all_chats', { method: 'POST' })
                .then(() => {
                    Swal.fire('Deleted!', 'All chats have been deleted.', 'success');
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
    st.session_state.current_chat = "Chat 1"
    st.session_state.pop("delete_all_chats")  # Reset the flag
    st.rerun()  # Refresh the app

# Button to trigger deletion in session state
# if st.sidebar.button("Confirm Delete All Chats (Debug)"):
    # st.session_state["delete_all_chats"] = True