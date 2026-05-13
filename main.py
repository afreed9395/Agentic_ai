from fastapi import FastAPI
from pydantic import BaseModel
from agent.agentic_workflow import GraphBuilder
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def travel_planner(query: QueryRequest):
    
    try:
        print(f"Received query: {query}")
        graph = GraphBuilder(model_provider = "openai")
        react_app = graph()
        png_graph = react_app.get_graph().draw_mermaid_png()

        with open("my_graph.png", "wb") as f:
            f.write(png_graph)

        print(f"graph saved as my_graph.png in the current working directory {os.getcwd()}")
        
        messages = {"messages": [query.query]}
        output = react_app.invoke(messages)

        if isinstance(output, dict) and "messages" in output:
            final_output = output["messages"][-1].content
        else:
            final_output = str(output)

        return JSONResponse(content={"response": final_output})        
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
        


