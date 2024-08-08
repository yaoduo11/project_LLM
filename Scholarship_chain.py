#import os, tempfile
#from pathlib import Path
from langchain_community.embeddings import FakeEmbeddings
from langchain.vectorstores import Chroma
from langchain.document_loaders import PyPDFLoader
#from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
#from langchain.embeddings.openai import OpenAIEmbeddings
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


class ScholarshipQA:
    def __init__(self, pdf_path, llm):
        self.pdf_path = pdf_path
        self.llm = llm
        self.loader_pdf = PyPDFLoader(pdf_path) 
        self.docs = self.loader_pdf.load()
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
        self.all_splits = self.text_splitter.split_documents(self.docs)
        self.vectorstore = Chroma.from_documents(documents=self.all_splits, embedding=FakeEmbeddings(size=1024))
        self.retriever = self.vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 12})
        
        self.Scholarshipchain_template = """
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. Use three sentences maximum and keep the "
            "answer concise."
            "\n\n"
            "{context}"
        """
        self.Scholarshipchain_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.Scholarshipchain_template),
                MessagesPlaceholder(variable_name='history'), 
                ("human", "{input}"),
            ]
        )
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        self.rag_chain = (
            RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
            | self.Scholarshipchain_prompt
            | self.llm
            | StrOutputParser()
        )

        self.retrieve_docs = (lambda x: x["input"]) | self.retriever

        self.Scholarshipchain_chain = RunnablePassthrough.assign(context=self.retrieve_docs).assign(
            answer=self.rag_chain
        )
    
    def get_chain(self):
        return self.Scholarshipchain_chain

