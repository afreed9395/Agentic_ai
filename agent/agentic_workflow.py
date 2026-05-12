from utils.models_loader import ModelLoader

from prompt_library.prompt import SYSTEM_PROMPT
from langgraph.graph import END, StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition




class GraphBuilder():

    def __init__(self):
        
        self.tools = [

        ]

        self.system_prompt = SYSTEM_PROMPT


    def agent_function(self, state:MessagesState):

        """ Main agent function """

        user_question = state["messages"]
        input_question = self.system_prompt + user_question
        response = self.llm_with_tools.invoke(input_question)
        return {"messages": [response]}
        
        
    def graph_builder(self):
        graph_builder = StateGraph(MessagesState)
        graph_builder.add_edge(START, "agent")
        graph_builder.add_node("agent", self.agent_function)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_conditional_edges("agents", tools_condition)
        graph_builder.add_edge("tools", "agent")
        graph_builder.add_edge("agent", END)
        
        self.graph = graph_builder.compile()
        return self.graph

    def __call__(self):
        return self.graph_builder()

