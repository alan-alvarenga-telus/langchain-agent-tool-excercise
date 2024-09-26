from typing import List, Union
from langchain.tools import BaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import render_text_description
from langchain_openai import ChatOpenAI
from agent_nulling_finder.processor import (
    get_account_number,
    get_central_account_number,
)
from langchain.schema import AgentAction, AgentFinish
from langchain.agents.output_parsers import ReActSingleInputOutputParser
import json


def find_tool_by_name(tools: List[BaseTool], tool_name: str) -> BaseTool:
    for internal_tool in tools:
        if internal_tool.name == tool_name:
            return internal_tool
    raise ValueError(f"Tool with name {tool_name} not found")


def mock_data():
    data = [
        {
            "account_id": "123456",
            "account_central_id": None,
            "account_owner": "John Doe",
        },
        {"account_id": None, "account_central_id": None, "account_owner": "Jane Smith"},
        {
            "account_id": "654321",
            "account_central_id": "CENTRAL_987",
            "account_owner": "Emily Johnson",
        },
        {
            "account_id": None,
            "account_central_id": "CENTRAL_543",
            "account_owner": "Michael Brown",
        },
        {
            "account_id": "345678",
            "account_central_id": None,
            "account_owner": "Olivia Davis",
        },
    ]
    return data


def get_template() -> str:
    return """
    Answer the following questions as best you can. You have access to the following tools:

    {tools}

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times if needed)
    Thought: If account_id is missing, fetch it using the relevant tool. If account_central_id is missing, fetch it using the relevant tool, either after fetching account_id if necessary or directly if account_id is present.
    Final Answer: the final answer to the original input question

    Begin!

    Question: {input}
    Thought: {agent_scratchpad}
    """


def fill_missing_properties():
    tool_collection: List[BaseTool] = [
        get_account_number,
        get_central_account_number,
    ]

    prompt = PromptTemplate.from_template(template=get_template()).partial(
        tools=render_text_description(tool_collection),
        tool_names=", ".join([t.name for t in tool_collection]),
    )

    llm = ChatOpenAI(temperature=0, stop=["\nObservation", "Observation"])
    intermediate_steps = []

    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: x["agent_scratchpad"],
        }
        | prompt
        | llm
        | ReActSingleInputOutputParser()
    )

    predicate = """
    Examine the following JSON object. If account_id is missing, use the relevant tool to fetch it. If account_central_id is missing, fetch it either after getting account_id or directly if account_id is already available.
    """

    updated_data = []

    for element in mock_data():
        print(f"Processing element: {element}")

        # Step 1: Use the agent to identify missing fields and decide the correct tool
        agent_step: Union[AgentAction, AgentFinish] = agent.invoke(
            {
                "input": f"{predicate} JSON object to examine {json.dumps(element)}",
                "agent_scratchpad": intermediate_steps,
            }
        )
        print(agent_step)
        # Step 2: Process the action, update the element dynamically
        if isinstance(agent_step, AgentAction):
            tool_name = agent_step.tool
            tool_to_use = find_tool_by_name(tool_collection, tool_name)
            tool_input = agent_step.tool_input
            observation = tool_to_use.func(str(tool_input))

            # Step 3: Update the element with the observation from the tool
            if tool_name == "get_account_number":
                element["account_id"] = observation
            elif tool_name == "get_central_account_number":
                element["account_central_id"] = observation

        # Step 4: Append the updated element to the result
        updated_data.append(element)

    # Step 5: Save the updated data to a new JSON file
    with open("filled_data.json", "w") as json_file:
        json.dump(updated_data, json_file, indent=4)

    print("Updated JSON file has been saved as 'filled_data.json'.")
