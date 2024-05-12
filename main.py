import argparse
import os
from typing import List
from openai.types.chat import ChatCompletionMessageParam
import openai
import chromadb
import anthropic
from dotenv import load_dotenv
import streamlit as st
load_dotenv()


class Message():
    def __init__(self,content:str,type:str):
        self.content=content
        self.type=type
    def get_content(self):
        return self.content
    def get_type(self):
        return self.type
    def set_content(self,content:str):
        self.content=content
    def set_type(self,type:str):
        self.type=type
    


    # Get the collection.

if 'init' not in st.session_state:
    
    st.session_state['init']=True
    client = chromadb.PersistentClient(path='chroma_storage')
    collection = client.get_collection(name='file1_collection')
    st.session_state['collection']=collection
    st.session_state['client']=client
    st.session_state['input_usage']=0
    st.session_state['output_usage']=0
    st.session_state['total_usage']=0
    st.session_state['existing_files']=set()
    



os.environ["TOKENIZERS_PARALLELISM"] = "false"



def get_anthropic_response(query: str) -> str:
    """
    Queries the GPT API to get a response to the question.

    Args:
    query (str): The original query.
    context (List[str]): The context of the query, returned by embedding search.

    Returns:
    A response to the question.
    """
    results = st.session_state.collection.query(
            query_texts=[query], n_results=10, include=["documents", "metadatas","distances"],
        )
        
    
    context=results["documents"][0]
    client=anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )
    response = client.messages.create(
        # model="claude-3-opus-20240229",
        model='claude-3-haiku-20240307',
        max_tokens=1000,
        temperature=0.2  ,
        system=f"""
        I am going to ask you a question, which I would like you to answer"
        "based only on the provided context, and not any other information."
        "If there is not enough information in the context to answer the question,"
        'say "I am not sure", then try to make a guess.'
        "Break your answer up into nicely readable paragraphs.
        here is all the context you have:{context}"
        """,
        messages=[
            {"role": "user", "content": query}
        ]
    )
    st.write(response.content[0].text)
    
    st.session_state.input_usage+=response.usage.input_tokens
    st.session_state.output_usage+=response.usage.output_tokens
    st.session_state.total_usage+=st.session_state.input_usage+st.session_state.output_usage
    

def write_side_bar():
    with st.sidebar:
        
        st.markdown("## Input Usage: ")
        st.write(st.session_state.input_usage)
        st.markdown("## Output Usage: ")
        st.write(st.session_state.output_usage)
        st.markdown("## Total Usage: ")
        st.write(st.session_state.total_usage)
        for file_name in st.session_state.collection.get()['metadatas']:
            if file_name['filename'] not in st.session_state.existing_files:
                st.write(file_name['filename'])
                st.session_state.existing_files.add(file_name['filename'])
        # for line in st.session_state.collection.get()['metadatas']:
        #     st.session_state.existing_files.add(line['filename'])
        # for file in st.session_state.existing_files:
        #     st.write(file)

def display_chat_history():
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history']=[]
        m1=Message("hello","ai")
        m2=Message("hi","user")
        st.session_state['chat_history'].append(m1)
        st.session_state['chat_history'].append(m2)
    ai=st.chat_message("ai")
    user=st.chat_message("user")
    for i in st.session_state['chat_history']:
        if i.get_type()=='ai':
            st.chat_message("ai").write(i.get_content())
        else:
            st.chat_message("user").write(i.get_content())
def main() -> None:
    st.title("Anthropic RAG Chat")
    write_side_bar()
    query=st.chat_input("send a message")
    if query:
        get_anthropic_response(query)
        
    display_chat_history()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load documents from a directory into a Chroma collection"
    )
    parser.add_argument(
        "--persist_directory",
        type=str,
        default="chroma_storage",
        help="The directory where you want to store the Chroma collection",
    )
    parser.add_argument(
        "--collection_name",
        type=str,
        default="documents_collection",
        help="The name of the Chroma collection",
    )
    # Parse arguments
    args = parser.parse_args()
    main()
