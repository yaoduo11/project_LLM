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


class PhdguidQA:
    def __init__(self, pdf_path, llm,collection_name):
        self.pdf_path = pdf_path
        self.llm = llm
        self.collection_name=collection_name
        self.loader_pdf = PyPDFLoader(pdf_path) 
        self.docs = self.loader_pdf.load()
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        self.all_splits = self.text_splitter.split_documents(self.docs)
        self.vectorstore = Chroma.from_documents(collection_name=collection_name,documents=self.all_splits, embedding=FakeEmbeddings(size=1024))
        self.retriever = self.vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 12})
        
        self.phdguidchain_template = """
        "You are a PhD student guide assistant."
        "Use the following retrieved context to answer the question." 
        "Don't appear to as stated in Xxxx"
        "Ensure your response is logically organized. "
        "According to user input ,response answer is very concise and precise.and No more than four lines "
        "Answers are presented in a format that is comfortable for the user to view."
        
        "\n\n"
        "{context}"
        """
        self.phdguidchain_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.phdguidchain_template),
                MessagesPlaceholder(variable_name='history'), 
                ("human", "{input}"),
            ]
        )
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        self.rag_chain = (
            RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
            | self.phdguidchain_prompt
            | self.llm
            | StrOutputParser()
        )

        self.retrieve_docs = (lambda x: x["input"]) | self.retriever

        self.phdguidchain = RunnablePassthrough.assign(context=self.retrieve_docs).assign(
            answer=self.rag_chain
        )
    
    def get_chain(self):
        return self.phdguidchain

