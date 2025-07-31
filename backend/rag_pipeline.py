from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_pinecone import Pinecone as LangchainPinecone
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import re
import nomic
from nomic import embed
from pinecone import Pinecone,ServerlessSpec

load_dotenv()

nomic.login(os.getenv("NOMIC_EMBEDDINGS_API_KEY"))

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

class CustomNomicEmbeddings:
    def embed_query(self, text: str):
        result = embed.text(
            texts=[text],
            model='nomic-embed-text-v1.5',
            task_type='search_query'
        )
        return result['embeddings'][0]
    def embed_documents(self, texts):
        result = embed.text(
            texts=texts,
            model='nomic-embed-text-v1.5',
            task_type='search_document'
        )
        return result['embeddings']

class RAGPipeline:
    def __init__(self,index_name: str = "page-pilot"):
        self.index_name = index_name
        self.embeddings = CustomNomicEmbeddings()
        if index_name not in pc.list_indexes().names():
            pc.create_index(
                name = index_name,
                dimension = 768, #dimension of vectors produced by nomic-embed-text
                metric = "cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
        self.index = pc.Index(index_name) #Low level connection library
        self.vectorstore = LangchainPinecone.from_existing_index(
            index_name=self.index_name,
            embedding=self.embeddings
        )
        self.llm = ChatGoogleGenerativeAI(
            model = "gemini-2.5-flash",
            google_api_key = os.getenv("GEMINI_API_KEY")
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = 1000,
            chunk_overlap = 200,
            length_function = len
        )
    
    async def extract_webpage_content(self,url:str):
        try:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url = url)
                if result.success:
                    content = result.markdown
                    content = re.sub(r'\s+', ' ', content)
                    content = re.sub(r'\n+', '\n', content)
                    print(f"=== SCRAPED CONTENT FROM {url} ===")
                    print(f"Content length: {len(content)} characters")
                    print(f"First 500 characters: {content[:500]}...")
                    print("=== END SCRAPED CONTENT ===")
                    return content.strip()
                else:
                    print(f"Failed to scrape {url}")
                    return ""
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return ""
        
    async def process_webpage_content(self,content:str,url:str):
        try:
            if not content.strip():
                return {"status":"error","message":"No content to process"}
            
            doc = Document(
                page_content=content,
                metadata = {
                    "source":url
                }
            )   
            chunks = self.text_splitter.split_documents([doc]) #split into chunks
            if not chunks:
                return {"status": "error"}

            print(f"=== PROCESSING CHUNKS FOR {url} ===")
            print(f"Number of chunks created: {len(chunks)}")
            for i, chunk in enumerate(chunks[:2]):  # Show first 2 chunks only
                print(f"Chunk {i+1} (length: {len(chunk.page_content)}): {chunk.page_content[:200]}...")
            print("=== END CHUNKS ===")

            texts = [chunk.page_content for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]
            ids = [f"{url}_{i}" for i in range(len(chunks))]

            self.vectorstore.add_texts(
                texts = texts,
                metadatas=metadatas,
                ids = ids
            )
            return {
                "status": "success"
            }
        except Exception as e:
                print(f"Error processing content: {e}")
                return {"status": "error"}
    
    async def query_rag(self,question:str):
        try:
            search_kwargs = {"k":3}
            retriever = self.vectorstore.as_retriever(search_kwargs = search_kwargs)
            prompt_template = """
            You are a helpful AI assistant that answers questions based on webpage content.
            Use the following pieces of context to answer the question at the end.

            Format your response clearly:
            - Use bullet points for lists
            - Break information into short paragraphs
            - Use numbers for step-by-step instructions
            - Keep sentences concise and readable
                        
            Context: {context}
            
            Question: {question}
            
            Answer:"""
            
            PROMPT = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "question"]
            )

            qa_chain = RetrievalQA.from_chain_type(
                llm = self.llm,
                chain_type = "stuff",
                retriever = retriever,
                chain_type_kwargs = {"prompt":PROMPT},
                return_source_documents = True
            )

            print(f"=== QUERY: {question} ===")
            result = qa_chain.invoke({"query":question})
            
            # Print the context that was retrieved
            if "source_documents" in result:
                print("=== RETRIEVED CONTEXT ===")
                for i, doc in enumerate(result["source_documents"]):
                    print(f"Document {i+1}: {doc.page_content[:300]}...")
                    print(f"Source: {doc.metadata.get('source', 'Unknown')}")
                print("=== END CONTEXT ===")
            
            print(f"=== AI ANSWER ===")
            print(f"Answer: {result['result']}")
            print("=== END ANSWER ===")
            
            return {
                "answer": result["result"] 
            }
        except Exception as e:
            print(f"Error in query_rag: {e}")
            return {
                "answer": f"Error processing your question: {str(e)}"
            }
        
    async def process_url_and_store(self, url):
        try:
            content = await self.extract_webpage_content(url)
            if not content:
                return {"status": "error"}
            result = await self.process_webpage_content(content, url)
            return result
            
        except Exception as e:
            return {"status": "error"}
        
    async def clear_content_by_source(self, url: str):
        try:
            self.index.delete(filter={"source": url})
            return {"status": "success"}
        except Exception as e:
            return {"status": "error"}
        
rag_pipeline = RAGPipeline()

async def create_rag(url: str):
    try:
        result = await rag_pipeline.process_url_and_store(url)
        return result["status"]
    except Exception as e:
        return "error"
    
async def query_rag_pipeline(question: str):
    try:
        result = await rag_pipeline.query_rag(question)
        return result
    except Exception as e:
        return {
            "answer": f"Error: {str(e)}"
        }
async def clear_rag_data(url:str):
    try:
        result = await rag_pipeline.clear_content_by_source(url)
        return result["status"]
    except Exception as e:
        return "error"
