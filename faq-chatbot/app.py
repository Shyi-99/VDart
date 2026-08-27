# Streamlit web interface.
#
# Run with:
#     streamlit run app.py

import streamlit as st
import chatbot

st.set_page_config(page_title="FAQ Chatbot", page_icon="💬")

st.title("💬 FAQ Chatbot")
st.caption("Ask a question and I will answer using our FAQ.")

# Keep the chat history for this browser session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show the messages we already have
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["text"])

        # Show which FAQ entries the answer came from
        if message.get("sources"):
            with st.expander("See the FAQ entries used"):
                for source in message["sources"]:
                    st.write(source)
                    st.divider()

# The input box at the bottom
question = st.chat_input("Type your question here...")

if question:
    # Show the user's question
    st.session_state.messages.append({"role": "user", "text": question})
    with st.chat_message("user"):
        st.write(question)

    # Get the answer
    with st.chat_message("assistant"):
        with st.spinner("Searching the FAQ..."):
            result = chatbot.get_answer(question)

        st.write(result["answer"])

        if result["sources"]:
            with st.expander("See the FAQ entries used"):
                for source in result["sources"]:
                    st.write(source)
                    st.divider()

    st.session_state.messages.append({
        "role": "assistant",
        "text": result["answer"],
        "sources": result["sources"],
    })

# Sidebar
with st.sidebar:
    st.subheader("About")
    st.write(
        "This chatbot uses RAG (Retrieval-Augmented Generation). "
        "It searches the FAQ for the most relevant entries, then asks "
        "Gemini to answer using only those entries."
    )
    st.write("If the FAQ does not cover your question, it will say so "
             "instead of guessing.")

    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()
