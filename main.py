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
    def __init__(self):
        self.content=''
        self.type=''
    def get_content(self):
        return self.content
    def get_type(self):
        return self.type


os.environ["TOKENIZERS_PARALLELISM"] = "false"



def get_anthropic_response(query: str, context: List[str]) -> str:
    """
    Queries the GPT API to get a response to the question.

    Args:
    query (str): The original query.
    context (List[str]): The context of the query, returned by embedding search.

    Returns:
    A response to the question.
    """
    client=anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )
    message = client.messages.create(
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
    return {'content':message.content[0].text,'usage':message.usage}

def write_side_bar():
    with st.sidebar:
        
        st.markdown("## Input Usage: ")
        st.write(st.session_state.input_usage)
        st.markdown("## Output Usage: ")
        st.write(st.session_state.output_usage)
        st.markdown("## Total Usage: ")
        st.write(st.session_state.total_usage)
        for line in st.session_state.collection.get()['metadatas']:
            st.session_state.existing_files.add(line['filename'])
        for file in st.session_state.existing_files:
            st.write(file)
def load_data_base(
    collection_name: str = "documents_collection", persist_directory: str = "."
) -> None:
    

    
    client = chromadb.PersistentClient(path=persist_directory)

    # Get the collection.
    collection = client.get_collection(name=collection_name)

    #init
    st.session_state['collection']=collection
    st.session_state['client']=client
    st.session_state['input_usage']=0
    st.session_state['output_usage']=0
    st.session_state['total_usage']=0
    st.session_state['existing_files']=set()
    st.session_state['init']=True
    
    st.title("Anthropic RAG Chat")
    user=st.chat_message("user")
    ai=st.chat_message("ai")
    user.write("Hello")
    ai.write("how can I help you?")
    # if st.session_state.init==True:
    #     st.session_state.init=False
    #     write_side_bar()



    query=st.chat_input("send a message")
    if query:
        results = collection.query(
            query_texts=[query], n_results=10, include=["documents", "metadatas","distances"],
        )
        
        sources=[]
        for i in results["metadatas"][0]:
            sources.append((i["filename"],i["page_number"]))
        response=get_anthropic_response(query,results["documents"][0])
        st.write(response['content'])
        
        st.session_state.input_usage=response['usage'].input_tokens+st.session_state.input_usage
        st.session_state.output_usage=response['usage'].output_tokens+st.session_state.output_usage
        st.session_state.total_usage=st.session_state.input_usage+st.session_state.output_usage+st.session_state.total_usage

        st.write("\n")
        st.write(f"Source documents:\n")
        # st.write(results["documents"][0])
        for k,v in sources:
            st.write(f"{k} : page number {v+1}")
        st.write("\n")
        write_side_bar()

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
    load_data_base(collection_name='file1_collection',persist_directory=args.persist_directory)
