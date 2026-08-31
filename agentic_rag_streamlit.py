# import basics
import os
from dotenv import load_dotenv

# import streamlit
import streamlit as st

# import langchain
from langchain_classic.agents import AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_classic.agents import create_tool_calling_agent
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.tools import tool

# import supabase db
from supabase.client import Client, create_client

# load environment variables
load_dotenv()  

# initiating supabase
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set.")

supabase: Client = create_client(supabase_url, supabase_key)

# initiating embeddings model
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# initiating vector store
vector_store = SupabaseVectorStore(
    embedding=embeddings,
    client=supabase,
    table_name="documents",
    query_name="match_documents",
)
 
# initiating llm
llm = ChatOpenAI(model="gpt-4o",temperature=0)

# define the agent prompt locally
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You answer questions using the available document retrieval tool. "
            "Use retrieved context when it is relevant, and say when the documents do not contain the answer.",
        ),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


# creating the retriever tool
@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """Retrieve information related to a query."""
    retrieved_docs = vector_store.similarity_search(query, k=2)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs

# combining all tools
tools = [retrieve]

# initiating the agent
agent = create_tool_calling_agent(llm, tools, prompt)

# create the agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# initiating streamlit app
st.set_page_config(
    page_title="Syntronic Labs | Knowledge System",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');

        :root {
            --ink: #090a0c;
            --panel: #121416;
            --line: #2d3034;
            --paper: #f2f0e9;
            --muted: #9a9d9e;
            --signal: #ff4d35;
            --active: #caee4f;
        }

        .stApp {
            background:
                linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px),
                linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
                var(--ink);
            background-size: 48px 48px;
            color: var(--paper);
            font-family: 'Space Grotesk', sans-serif;
        }

        #MainMenu, footer, header { visibility: hidden; }
        .block-container { max-width: 1120px; padding-top: 2.25rem; padding-bottom: 7rem; }
        [data-testid="stSidebar"] { background: #0d0f11; border-right: 1px solid var(--line); }
        [data-testid="stSidebar"] > div:first-child { padding: 1.5rem 1.15rem; }
        [data-testid="stSidebar"] * { font-family: 'DM Mono', monospace; }

        .wordmark { color: var(--paper); font: 700 1rem 'Space Grotesk', sans-serif; letter-spacing: 0; }
        .wordmark span { color: var(--signal); }
        .eyebrow, .sidebar-label, .message-label {
            color: var(--muted); font: 500 .67rem 'DM Mono', monospace;
            letter-spacing: .08em; text-transform: uppercase;
        }
        .system-header { border-bottom: 1px solid var(--line); margin-bottom: 2.5rem; padding-bottom: 1.25rem; }
        .system-title { color: var(--paper); font: 700 clamp(2rem, 5vw, 4rem) 'Space Grotesk', sans-serif; line-height: .95; margin: .45rem 0 0; }
        .system-title em { color: var(--signal); font-style: normal; }
        .system-subtitle { color: var(--muted); font-size: .95rem; margin: 1rem 0 0; max-width: 40rem; }
        .status { align-items: center; display: flex; gap: .55rem; color: var(--paper); font: 500 .68rem 'DM Mono', monospace; margin: 1.3rem 0 2rem; }
        .status-dot { background: var(--active); border-radius: 50%; box-shadow: 0 0 12px var(--active); height: 7px; width: 7px; }
        .empty-state { border-left: 2px solid var(--signal); margin: 3rem 0 1rem; padding: .3rem 0 .3rem 1.25rem; }
        .empty-state h2 { color: var(--paper); font: 600 1.35rem 'Space Grotesk', sans-serif; margin: 0; }
        .empty-state p { color: var(--muted); margin: .5rem 0 0; }

        [data-testid="stChatMessage"] { background: transparent; border: 1px solid var(--line); border-radius: 0; margin: 1rem 0; padding: 1rem 1.1rem; }
        [data-testid="stChatMessage"] p { color: var(--paper); font-family: 'Space Grotesk', sans-serif; }
        [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"] { background: var(--signal); }
        [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] { background: var(--active); color: var(--ink); }
        [data-testid="stChatInput"] { border: 1px solid var(--line); border-radius: 0; background: var(--panel); }
        [data-testid="stChatInput"] textarea { color: var(--paper); font-family: 'Space Grotesk', sans-serif; }
        [data-testid="stChatInput"] textarea::placeholder { color: var(--muted); }
        [data-testid="stChatInput"] button { color: var(--signal); }
        .stButton > button { border: 1px solid var(--line); border-radius: 0; color: var(--paper); background: transparent; font-size: .72rem; letter-spacing: .05em; text-transform: uppercase; width: 100%; }
        .stButton > button:hover { border-color: var(--signal); color: var(--signal); }
        @media (max-width: 640px) { .block-container { padding: 1.5rem 1rem 6rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<div class="wordmark">SYNTRONIC <span>LABS</span></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="sidebar-label">Knowledge system</p>', unsafe_allow_html=True)
    st.markdown("Document-grounded AI for focused research and retrieval.")
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Clear session"):
        st.session_state.messages = []
        st.rerun()

st.markdown(
    """
    <section class="system-header">
        <p class="eyebrow">Research interface / 01</p>
        <h1 class="system-title">Context, <em>retrieved.</em></h1>
        <p class="system-subtitle">Ask questions against the documents indexed in this knowledge system.</p>
    </section>
    <div class="status"><span class="status-dot"></span> SYSTEM READY · SUPABASE VECTOR INDEX</div>
    """,
    unsafe_allow_html=True,
)

# initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown(
        """
        <div class="empty-state">
            <h2>What do you need to know?</h2>
            <p>Start a conversation below. Responses are grounded in the indexed document collection.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# display chat messages from history on app rerun
for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(message.content)


# create the bar where we can type messages
user_question = st.chat_input("Ask the knowledge system")


# did the user submit a prompt?
if user_question:

    # add the message from the user (prompt) to the screen with streamlit
    with st.chat_message("user"):
        st.markdown(user_question)

        st.session_state.messages.append(HumanMessage(user_question))


    # invoking the agent
    result = agent_executor.invoke({"input": user_question, "chat_history":st.session_state.messages})

    ai_message = result["output"]

    # adding the response from the llm to the screen (and chat)
    with st.chat_message("assistant"):
        st.markdown(ai_message)

        st.session_state.messages.append(AIMessage(ai_message))

