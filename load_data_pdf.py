import os
import argparse
from tqdm import tqdm
import chromadb
import PyPDF2

def read_pdf(file_path: str) -> str:
    res=[]
    pages=PyPDF2.PdfReader(file_path).pages
    for page in pages:
        res.append(page.extract_text())
    return res

def main(documents_directory: str = "documents",collection_name: str = "documents_collection",persist_directory: str = ".",) -> None:
    # Read all files in the data directory
    documents = []
    metadatas = []
    files = os.listdir(documents_directory)
    # Instantiate a persistent chroma client in the persist_directory.
    # Learn more at docs.trychroma.com
    client = chromadb.PersistentClient(path=persist_directory)

    # If the collection already exists, we just return it. This allows us to add more
    # data to an existing collection.
    collection = client.get_or_create_collection(name=collection_name)
    existing_files=set()
    for line in collection.get()['metadatas']:
        existing_files.add(line['filename'])
    files=os.listdir(documents_directory)
    for filename in files:
        if filename not in existing_files:
            pages=read_pdf(f"{documents_directory}/{filename}")
            print(pages)
            for page_number,page in enumerate(pages):
                
                if len(page) == 0:
                        continue
                documents.append(page)
                metadatas.append({"filename": filename, "page_number": page_number})
    # Create ids from the current count
    count = collection.count()
    print(f"Collection already contains {count} documents")
    ids = [str(i) for i in range(count, count + len(documents))]
    for i in range(0,len(documents)):
        collection.add(ids=ids[i],documents=documents[i],metadatas=metadatas[i])
    new_count = collection.count()
    print(f"Added {new_count-count} documents to the collection")
    
if __name__ == "__main__":
    # Read the data directory, collection name, and persist directory
    parser = argparse.ArgumentParser(
        description="Load documents from a directory into a Chroma collection"
    )

    # Add arguments
    parser.add_argument(
        "--data_directory",
        type=str,
        default="documents",
        help="The directory where your text files are stored",
    )
    parser.add_argument(
        "--collection_name",
        type=str,
        default="documents_collection",
        help="The name of the Chroma collection",
    )
    parser.add_argument(
        "--persist_directory",
        type=str,
        default="chroma_storage",
        help="The directory where you want to store the Chroma collection",
    )

    # Parse arguments
    args = parser.parse_args()

    main(
        documents_directory='documents',
        collection_name='file1_collection',
        persist_directory='chroma_storage',
    )
    