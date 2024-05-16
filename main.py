import argparse
import os
from typing import List
from openai.types.chat import ChatCompletionMessageParam
import openai
import chromadb
import anthropic
from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai
import os

#--------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------#
GOOGLE_API_KEY=os.environ.get('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
os.environ["TOKENIZERS_PARALLELISM"] = "false"
load_dotenv()

#--------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------#
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
    

#--------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------#

def init():
    
    
    st.session_state['init']=True
    db_client = chromadb.PersistentClient(path='chroma_storage')
    collection = db_client.get_collection(name='file1_collection')
    st.session_state['collection']=collection
    anthropic_client=anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    st.session_state['anthropic_client']=anthropic_client
    st.session_state['input_usage']=0
    st.session_state['output_usage']=0
    st.session_state['total_usage']=0
    st.session_state['existing_files']=set()
    st.session_state['chat_history']=[]
    st.session_state['chat_history'].append(Message("Hello, I am an AI assistant. How can I help you today?","ai"))
    
#--------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------#

def get_results(query: str) -> List[str]:
    results = st.session_state.collection.query(
        query_texts=[query], n_results=3, include=["documents", "metadatas","distances"],
    )
    return results['documents'][0]

#--------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------#

def filter_results(data):
    # Unpack data
    ids = data.get('ids', [])
    distances = data.get('distances', [])
    metadatas = data.get('metadatas', [])
    documents = data.get('documents', [])
    
    filtered_results = {'ids': [], 'distances': [], 'metadatas': [], 'documents': []}
    
    # Iterate over distances and filter based on the criteria
    for i, distance_list in enumerate(distances):
        for j, distance in enumerate(distance_list):
            if abs(1 - distance) < 0.4:
                filtered_results['ids'].append(ids[i][j])
                filtered_results['distances'].append(distance)
                filtered_results['metadatas'].append(metadatas[i][j])
                filtered_results['documents'].append(documents[i][j])
                
    return filtered_results

#--------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------#

def get_anthropic_response(query: str,context:list) -> str:
    
    
    
    
    response = st.session_state['anthropic_client'].messages.create(
        # model="claude-3-opus-20240229",
        model='claude-3-haiku-20240307',
        max_tokens=4000,
        temperature=0.2,
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
    st.session_state['chat_history'].append(Message(query,'user'))
    st.session_state['chat_history'].append(Message(response.content[0].text,'ai'))
    
    st.session_state.input_usage+=response.usage.input_tokens
    st.session_state.output_usage+=response.usage.output_tokens
    st.session_state.total_usage+=st.session_state.input_usage+st.session_state.output_usage

#--------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------#
def write_side_bar():
    with st.sidebar:
        
        st.markdown("## Input Usage: ")
        st.write(st.session_state.input_usage)
        st.markdown("## Output Usage: ")
        st.write(st.session_state.output_usage)
        st.markdown("## Total Usage: ")
        st.write(st.session_state.total_usage)
        # st.write("## Existing Files: ",st.session_state.collection.get()['metadatas'])
        for file_name in st.session_state.collection.get()['metadatas']:
            if file_name['filename'] not in st.session_state.existing_files:
                # st.write(file_name['filename'])
                st.session_state.existing_files.add(file_name['filename'])
        for file in st.session_state.existing_files:
            st.write(file)
        
#--------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------#
def display_chat_history():

        
    st.write("number of objects in chat_history: ",len(st.session_state['chat_history']))
    if 'chat_history' in st.session_state:
        
        for i in st.session_state['chat_history']:
            if i.get_type()=='user':

                st.chat_message('user').write(i.get_content())
    
            elif i.get_type()=='ai':
                st.chat_message('assistant').write(i.get_content())
#--------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------#

def main() -> None:
    if 'init' not in st.session_state:
        init()
    st.title("Anthropic RAG Chat")
    
    query=st.chat_input("send a message")
    if query:
        context=get_results(query)
        get_anthropic_response(query,context)

    display_chat_history()
    write_side_bar()
#--------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------#

if __name__ == "__main__":
    main()





#legacy code
    # parser = argparse.ArgumentParser(
    #     description="Load documents from a directory into a Chroma collection"
    # )
    # parser.add_argument(
    #     "--persist_directory",
    #     type=str,
    #     default="chroma_storage",
    #     help="The directory where you want to store the Chroma collection",
    # )
    # parser.add_argument(
    #     "--collection_name",
    #     type=str,
    #     default="documents_collection",
    #     help="The name of the Chroma collection",
    # )
    # # Parse arguments
    # args = parser.parse_args()
