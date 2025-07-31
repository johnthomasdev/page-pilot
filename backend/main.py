from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,Field
from rag_pipeline import create_rag,query_rag_pipeline,clear_rag_data

app = FastAPI(
    title="Page Pilot Backend"
)

origins = [
    "chrome-extension://<enter your google extension id>" #Replace with your actual extension id!!!
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CreateRagRequest(BaseModel):
    url: str 

class CreateRagResponse(BaseModel):
    status: str

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str

class ClearRequest(BaseModel):
    url: str

class ClearResponse(BaseModel):
    status: str


@app.get('/')
async def root():
    return {"message":"Server is alive!"}

@app.post('/analyze',response_model= CreateRagResponse)
async def analyze_page(request: CreateRagRequest):
    try:
        result = await create_rag(url = request.url)
        if result == "success":
            return CreateRagResponse(
                status="success"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to analyze webpage: {result}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post('/chat',response_model = QueryResponse)
async def chat(request:QueryRequest):
    try:
        if not request.question.strip():
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty"
            )
        result = await query_rag_pipeline(question = request.question)
        return QueryResponse(
            answer=result.get("answer", "No answer found"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.delete('/clear',response_model = ClearResponse)
async def clear(request: ClearRequest):
    try:
        result = await clear_rag_data(url=request.url)
        if result == "success":
            return ClearResponse(status="success")
        
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to clear data: {result}"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

