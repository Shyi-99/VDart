# Streamlit web interface.
#
# Run with:
#     streamlit run app.py

import streamlit as st
import chatbot

st.set_page_config(page_title="Tonton FAQ Chatbot", page_icon="💬")

st.title("💬 Tonton FAQ Chatbot")
st.caption("Tanya soalan anda dan saya akan menjawab berdasarkan FAQ Tonton. "
           "You can also ask in English.")

# Example questions, shown only when the chat is empty
EXAMPLES = [
    "Macam mana nak batal langganan?",
    "Dah bayar tapi tak boleh tengok",
    "Kenapa masih ada iklan?",
]

# Keep the chat history for this browser session
if "messages" not in st.session_state:
    st.session_state.messages = []


def show_sources(sources):
    """Show which FAQ entries the answer came from."""
    if not sources:
        return
    with st.expander("Lihat entri FAQ yang digunakan / See FAQ entries used"):
        for source in sources:
            st.write(source)
            st.divider()


def answer_question(question):
    """Ask the chatbot and add both messages to the history."""
    st.session_state.messages.append({"role": "user", "text": question})

    with st.spinner("Mencari dalam FAQ..."):
        result = chatbot.get_answer(question)

    st.session_state.messages.append({
        "role": "assistant",
        "text": result["answer"],
        "sources": result["sources"],
    })


# Show the messages we already have
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["text"])
        show_sources(message.get("sources"))

# Example buttons, only on an empty chat
if not st.session_state.messages:
    st.write("**Cuba tanya:**")
    columns = st.columns(len(EXAMPLES))
    for column, example in zip(columns, EXAMPLES):
        if column.button(example, use_container_width=True):
            answer_question(example)
            st.rerun()

# The input box at the bottom
question = st.chat_input("Taip soalan anda di sini...")

if question:
    answer_question(question)
    st.rerun()

# Sidebar
with st.sidebar:
    st.subheader("Tentang / About")
    st.write(
        "Chatbot ini menggunakan RAG (Retrieval-Augmented Generation). "
        "Ia mencari entri FAQ yang paling berkaitan, kemudian meminta Gemini "
        "menjawab menggunakan entri tersebut sahaja."
    )
    st.write(
        "Jika FAQ tidak meliputi soalan anda, ia akan memberitahu anda "
        "dan bukan meneka jawapan."
    )

    if st.button("Kosongkan chat / Clear chat"):
        st.session_state.messages = []
        st.rerun()
