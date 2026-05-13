from typing import Optional, Any, Literal
from pydantic import BaseModel, Field
# from config.config import config
from langchain_openai import ChatOpenAI
from utils.configs_loader import load_config
from dotenv import load_dotenv      
load_dotenv()
import os


class ConfigLoader():
    def __init__(self):
        print(f"loading config...")
        self.config = load_config()

    def __getitem__(self,key):
        return self.config[key]



class ModelLoader(BaseModel):

    model_provider: Literal["openai","groq"] = Field(default = "openai")
    config : Optional[ConfigLoader] = Field(default = None, exclude = True)
    def model_post_init(self, __context:Any) ->None:
        self.config = ConfigLoader()
    class Config:
        arbitrary_types_allowed = True

    def load_llm(self):
        """
         Load and return the LLM model
         """
        if self.model_provider == "openai":
            print("LLM Loading... ")
            print(f"Loading llm from the provider {self.model_provider}")
            openai_api_key = os.getenv("OPENAI_API_KEY")
            model_name = self.config["llm"]["openai"]["model_name"]
            llm = ChatOpenAI(model=model_name, api_key=openai_api_key)
            return llm
