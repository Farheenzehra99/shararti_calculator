import os
from dotenv import load_dotenv
from agents import Agent, function_tool, Runner
from agents.extensions.models.litellm_model import LitellmModel 
import chainlit as cl
from collections import defaultdict   


# Load API Key
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "openrouter/meta-llama/llama-3.3-8b-instruct:free"

# Session-based history
user_history = defaultdict(list) 
# Fun calculator logic
@function_tool
def solve_math(expression: str) -> str:
    try:
        result = eval(expression, {"__builtins__": None}, {})
        return f"🧮 You tried `{expression}` and the result is **{result}**! You're good at this 🤓"
    except Exception as e:
        return f"❌ Oops! Couldn't solve that. Error: {str(e)}"

# Define Agent
agent = Agent(
    name="Shararti Calculator",
    instructions="You are a mischievous (shararti) calculator who solves math in English and always adds a fun twist to the answer!",
    model=LitellmModel(
        model=MODEL,
        base_url=BASE_URL,
        api_key=API_KEY
    ),
    tools=[solve_math]
)

# On chat start
@cl.on_chat_start
async def start():
    await cl.Message(
        content=(
            "# 🎉 **Shararti Calculator ** 🎉\n"
            "Created with ❤️ by **Syeda Farheen Zehra**\n\n"
            "Ask me any math question in English, and I'll solve it for you (shararti style!) 😄"
        )
    ).send()

# On message
@cl.on_message
async def on_message(message: cl.Message):
    user_id = getattr(cl.user_session, "get", lambda *a, **k: "default")("id", "default")
    # History command
    if message.content.lower() in ["history", "show history"]:
        history = user_history.get(user_id, [])
        if not history:
            await cl.Message(content="📭 No history yet. Start solving something!").send()
        else:
            history_text = "\n".join(
                [f"🔹 `{item['input']}` ➜ {item['output']}" for item in history]
            )
            await cl.Message(content=f"📚 **Your Shararti History:**\n\n{history_text}").send()
        return

    # Processing
    msg = cl.Message(content="🧠 Calculating... Hang on!")
    await msg.send()

    try:
        result = await Runner.run(agent, message.content)
        response = result.final_output
        msg.content = response
        await msg.update()

        # Save to history
        user_history.setdefault(user_id, []).append({
            "input": message.content,
            "output": response
        })

    except Exception as e:
        msg.content = f"❌ Error: {str(e)}"
        await msg.update()
