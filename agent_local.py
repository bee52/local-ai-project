import datetime
import logging

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_ollama import ChatOllama

from app.config import settings
from app.logging_config import configure_logging
from app.services.agent_service import AgentService



configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

@tool
def get_current_datetime(format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Returns the current date and time, formatted according to the provided Python strftime format string.
    Use this tool whenever the user asks for the current date, time, or both.
    Example format strings: '%Y-%m-%d' for date, '%H:%M:%S' for time.
    If no format is specified, defaults to '%Y-%m-%d %H:%M:%S'.
    """
    try:
        return datetime.datetime.now(tz=datetime.timezone.utc).strftime(format)
    except (TypeError, ValueError) as exc:
        return f"Error formatting date/time: {exc}"

# list of tools agent can use
tools = [get_current_datetime]
logger.info("Custom tool defined")

def get_agent_llm(model_name=None, temperature=0):
    """
    Initializes the Ollama LLM for the agent.
    """
    model_name = model_name or settings.chat_model
    llm = ChatOllama(
        model=model_name, 
        base_url=settings.ollama_base_url,
        temperature=temperature,
        # num_ctx=8192  # context window size. Consider increasing if you need to handle larger contexts.
        )
    logger.info("Initialized Ollama LLM", extra={"model": model_name, "temperature": temperature})
    return llm

# agent_llm = get_agent_llm()


def get_agent_prompt(prompt_hub_name="hwchase17/openai-tools-agent"):
    """
    Returns the system prompt used by the agent.
    """
    prompt = (
        "You are a helpful assistant. Use the available tools when they help answer "
        "the user's question."
    )
    logger.info("Using local system prompt for the agent")
    return prompt

# agent_prompt = get_agent_prompt() # Call this later

def build_agent(llm, tools, prompt):
    """
    Builds the tool-calling agent using the provided LLM, tools, and prompt.
    """
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=prompt
    )
    logger.info("Agent runnable created")
    return agent

# agetn_runnable = build_agent(agent_llm, tools, agent_prompt) # Call this later

def create_agent_executor(agent, tools, verbose=True):
    """
    Returns the compiled agent graph.
    """
    logger.info("Agent graph created")
    return agent

# agent_executor = create_agent_executor(agent_runnable, tools) # Call this 

def run_agent(executor, user_input):
    """Runs the agent executor with the given input. """
    logger.info("Invoking agent", extra={"input": user_input})
    return AgentService(executor).answer(user_input)

# ----- Main Execution -----
if __name__ == "__main__":
    # 1. Define tools (already defined above)

    # 2. Get agent LLM
    agent_llm = get_agent_llm()

    # 3. Get agent prompt
    agent_prompt = get_agent_prompt()


    # 4. Build agent runnable 
    agent_runnable = build_agent(agent_llm, tools, agent_prompt)  


    # 5. Create agent executor
    agent_executor = create_agent_executor(agent_runnable, tools)


    # run agent
    print(run_agent(agent_executor, "What is the current date and time?"))
    
    print(run_agent(agent_executor, "What time is it right now? Use HH:MM format."))
    
    print(run_agent(agent_executor, "Tell me a joke."))