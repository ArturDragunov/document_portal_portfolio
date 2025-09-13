import sys
import os
import streamlit as st
from dotenv import load_dotenv
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.vectorstores import FAISS
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from utils.model_loader import ModelLoader
from exception.custom_exception import DocumentPortalException
from logger.custom_logger import CustomLogger
from prompt.prompt_library import PROMPT_REGISTRY
from model.models import PromptType

load_dotenv()

# Step-by-Step Breakdown
# Step 1: create_history_aware_retriever -> it is like Message state in langgraph
# What it does:
# Takes your current question + chat history → Creates a better search query → Finds relevant documents
# The Problem it Solves:
# # Without history awareness:
# User: "What is machine learning?"
# Bot: [searches for "machine learning", finds docs, answers]

# User: "What are its applications?"  # ❌ "its" refers to what?
# Bot: [searches for "what are its applications" - confusing!]

# # With history awareness:
# User: "What is machine learning?"
# Bot: [searches for "machine learning", finds docs, answers]

# User: "What are its applications?"  
# Bot: [combines question + history → searches for "machine learning applications" ✅]
      
# Manual Alternative:
# def manual_history_aware_retriever(question, chat_history, llm, retriever, contextualize_prompt):
#     # Step 1: Create standalone question from history
#     history_text = "\n".join([f"Human: {h['human']}\nAI: {h['ai']}" for h in chat_history])
    
#     contextualize_input = {
#         "chat_history": history_text,
#         "question": question
#     }
    
#     # Step 2: Use LLM to rephrase question with context
#     standalone_question = llm.invoke(contextualize_prompt.format(**contextualize_input))
    
#     # Step 3: Search with the improved question
#     relevant_docs = retriever.get_relevant_documents(standalone_question)
    
#     return relevant_docs      

# Step 2: create_stuff_documents_chain
# What it does:
# Takes retrieved documents + user question → Combines them into one prompt → Sends to LLM for answer
# The "Stuff" Strategy:

# "Stuff" = Put ALL retrieved documents into one big prompt
# Alternative strategies: "Map-Reduce", "Refine", "Map-Rerank"

# Step 3: create_retrieval_chain
# What it does:
# Combines the two previous chains into one pipeline:
# Question → History-Aware Retrieval → Document Stuffing → Final Answer

# Usually people use LCEL though: LangChain Expression Language
# e.g. # LCEL Style (Industry Standard)
# chain = prompt | llm | retriever | output_parser
class ConversationalRAG:
    def __init__(self, session_id: str, retriever):
        self.log = CustomLogger().get_logger(__name__)
        self.session_id = session_id
        self.retriever = retriever

        try:
            self.llm = self._load_llm()
            self.contextualize_prompt = PROMPT_REGISTRY[PromptType.CONTEXTUALIZE_QUESTION.value]
            self.qa_prompt = PROMPT_REGISTRY[PromptType.CONTEXT_QA.value]

            self.history_aware_retriever = create_history_aware_retriever(
                self.llm, self.retriever, self.contextualize_prompt
            )
            self.log.info("Created history-aware retriever", session_id=session_id)

            self.qa_chain = create_stuff_documents_chain(self.llm, self.qa_prompt)
            self.rag_chain = create_retrieval_chain(self.history_aware_retriever, self.qa_chain)
            self.log.info("Created RAG chain", session_id=session_id)


    # RunnableWithMessageHistory wraps another Runnable and manages the chat message
    # history for it; it is responsible for reading and updating the chat message
    # history.
            self.chain = RunnableWithMessageHistory(
                self.rag_chain,
                self._get_session_history, # our conversation is recorded under a session in streamlit 
                input_messages_key="input",
                history_messages_key="chat_history",
                output_messages_key="answer" # we define keys for dict which will hold our conversation
                # {'chat_history':'...','input':'...', 'answer':'...'}
            )
            self.log.info("Wrapped chain with message history", session_id=session_id)

        except Exception as e:
            self.log.error("Error initializing ConversationalRAG", error=str(e), session_id=session_id)
            raise DocumentPortalException("Failed to initialize ConversationalRAG", sys)

    def _load_llm(self): # private method -> we call it only inside other master method. e.g. here in __init__
        try:
            llm = ModelLoader().load_llm()
            self.log.info("LLM loaded successfully", class_name=llm.__class__.__name__)
            return llm
        except Exception as e:
            self.log.error("Error loading LLM via ModelLoader", error=str(e))
            raise DocumentPortalException("Failed to load LLM", sys)

    def _get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        # we are tracking session history using streamlit
        try:
            if "store" not in st.session_state:
                st.session_state.store = {}

            if session_id not in st.session_state.store:
                st.session_state.store[session_id] = ChatMessageHistory()
                self.log.info("New chat session history created", session_id=session_id)

            return st.session_state.store[session_id]
        except Exception as e:
            self.log.error("Failed to access session history", session_id=session_id, error=str(e))
            raise DocumentPortalException("Failed to retrieve session history", sys)

    def load_retriever_from_faiss(self, index_path: str):
        try:
            embeddings = ModelLoader().load_embeddings()
            if not os.path.isdir(index_path): # no vectore storage
                raise FileNotFoundError(f"FAISS index directory not found: {index_path}")

            vectorstore = FAISS.load_local(index_path, embeddings)
            self.log.info("Loaded retriever from FAISS index", index_path=index_path)
            return vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})

        except Exception as e:
            self.log.error("Failed to load retriever from FAISS", error=str(e))
            raise DocumentPortalException("Error loading retriever from FAISS", sys)
        
    def invoke(self, user_input: str) -> str:
        """The config parameter in invoke() is configuring session management for the chain.
            The {"configurable": {"session_id": self.session_id}} tells the chain:

            Which conversation session this request belongs to
            Enables the chain to maintain conversation history/context across multiple calls
            Allows the chain to store and retrieve session-specific state (like chat memory)

            This is typically used with LangChain's conversational chains that have memory components.
            The session_id acts as a key to separate different user conversations, so each user gets their own isolated chat history.
            Without this config, each invoke() call would be stateless - no memory of previous messages in the conversation.
        """
        try:
            response = self.chain.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": self.session_id}}
            )
            answer = response.get("answer", "No answer.")

            if not answer:
                self.log.warning("Empty answer received", session_id=self.session_id)

            self.log.info("Chain invoked successfully", session_id=self.session_id, user_input=user_input, answer_preview=answer[:150])
            return answer

        except Exception as e:
            self.log.error("Failed to invoke conversational RAG", error=str(e), session_id=self.session_id)
            raise DocumentPortalException("Failed to invoke RAG chain", sys)
