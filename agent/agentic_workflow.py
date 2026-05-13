from utils.models_loader import ModelLoader

from prompt_library.prompt import SYSTEM_PROMPT
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

from Tools.weather_info_tool import WeatherInfoTool
from Tools.place_search_tool import PlaceSearchTool
from Tools.currency_conversion_tool import CurrencyConversionTool
from Tools.calculator_tool import CalculatorTool




class GraphBuilder():

    def __init__(self,model_provider="openai"):
        self.model_loader = ModelLoader(model_provider = model_provider)
        self.llm = self.model_loader.load_llm()

        
        self.tools = []

        self.weather_tools = WeatherInfoTool()
        self.place_search_tools = PlaceSearchTool()
        self.currency_converter_tools = CurrencyConversionTool()
        self.calculator_tools = CalculatorTool()
        
        for tool_list in (
            self.weather_tools.weather_tool_list,
            self.place_search_tools.place_search_tool_list,
            self.currency_converter_tools.currency_converter_tool_list,
            self.calculator_tools.calculator_tool_list,
        ):
            self.tools.extend(tool_list)
        

        self.llm_with_tools = self.llm.bind_tools(tools = self.tools)

        self.system_prompt = SYSTEM_PROMPT


    def agent_function(self, state:MessagesState):

        """ Main agent function """

        # Do not use SystemMessage + list: in current LangChain that becomes ChatPromptTemplate,
        # which ChatOpenAI.invoke does not accept.
        normalized: list[BaseMessage] = []
        for m in state["messages"]:
            if isinstance(m, str):
                normalized.append(HumanMessage(content=m))
            else:
                normalized.append(m)
        input_messages = [self.system_prompt, *normalized]
        response = self.llm_with_tools.invoke(input_messages)
        return {"messages": [response]}

        
    def graph_builder(self):
        graph_builder = StateGraph(MessagesState)
        graph_builder.add_edge(START, "agent")
        graph_builder.add_node("agent", self.agent_function)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_conditional_edges("agent", tools_condition)
        graph_builder.add_edge("tools", "agent")
        graph_builder.add_edge("agent", END)
        
        self.graph = graph_builder.compile()
        return self.graph

    def __call__(self):
        return self.graph_builder()

