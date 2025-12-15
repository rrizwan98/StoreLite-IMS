# Model Configuration

Configure agents to use OpenAI models or LiteLLM with Gemini.

## OpenAI Models (Default)

### Basic OpenAI Usage

```python
from agents import Agent

# Uses default model (gpt-4o)
agent = Agent(
    name="DefaultAgent",
    instructions="Help users with their requests.",
)

# Specify model explicitly
agent = Agent(
    name="GPT4Agent",
    instructions="Help users with their requests.",
    model="gpt-4o",
)

# Use a specific model version
agent = Agent(
    name="GPT4oMiniAgent",
    instructions="Quick responses for simple tasks.",
    model="gpt-4o-mini",
)
```

### Available OpenAI Models

| Model | Best For |
|-------|----------|
| `gpt-4o` | General purpose, balanced quality/speed |
| `gpt-4o-mini` | Fast, cost-effective for simpler tasks |
| `gpt-4-turbo` | Complex reasoning, longer context |
| `o1` | Deep reasoning, multi-step problems |
| `o1-mini` | Reasoning with faster response |

## LiteLLM with Gemini

### Installation

```bash
pip install litellm openai-agents
```

### Environment Setup

```bash
export GEMINI_API_KEY=your-gemini-api-key
```

### Basic LiteLLM Usage

```python
from agents import Agent, Runner
from agents.extensions.models.litellm_model import LitellmModel

# Create LiteLLM model
gemini_model = LitellmModel(
    model="gemini/gemini-2.5-flash",
    api_key=os.environ["GEMINI_API_KEY"],
)

# Use with agent
agent = Agent(
    name="GeminiAgent",
    instructions="Help users with their requests.",
    model=gemini_model,
)

result = await Runner.run(agent, "What is machine learning?")
print(result.final_output)
```

### Available Gemini Models via LiteLLM

| Model String | Description |
|--------------|-------------|
| `gemini/gemini-2.5-flash` | Fast, efficient for most tasks |
| `gemini/gemini-2.5-pro` | Higher quality, more capable |
| `gemini/gemini-1.5-pro` | Previous generation, stable |

### Model Switching Strategy

```python
import os
from agents import Agent
from agents.extensions.models.litellm_model import LitellmModel

def get_model():
    """Get model based on environment configuration."""
    model_type = os.environ.get("MODEL_TYPE", "openai")
    
    if model_type == "gemini":
        return LitellmModel(
            model="gemini/gemini-2.5-flash",
            api_key=os.environ["GEMINI_API_KEY"],
        )
    elif model_type == "openai":
        return "gpt-4o"  # String for OpenAI models
    else:
        raise ValueError(f"Unknown model type: {model_type}")

agent = Agent(
    name="FlexibleAgent",
    instructions="Help users.",
    model=get_model(),
)
```

### Multi-Model Agent Factory

```python
from dataclasses import dataclass
from typing import Literal
from agents import Agent
from agents.extensions.models.litellm_model import LitellmModel

@dataclass
class ModelConfig:
    provider: Literal["openai", "gemini"]
    model_name: str
    api_key: str | None = None

def create_agent(
    name: str,
    instructions: str,
    config: ModelConfig,
    **kwargs
) -> Agent:
    """Create an agent with specified model configuration."""
    
    if config.provider == "gemini":
        model = LitellmModel(
            model=f"gemini/{config.model_name}",
            api_key=config.api_key,
        )
    else:
        model = config.model_name
    
    return Agent(
        name=name,
        instructions=instructions,
        model=model,
        **kwargs
    )

# Usage
openai_config = ModelConfig(provider="openai", model_name="gpt-4o")
gemini_config = ModelConfig(
    provider="gemini",
    model_name="gemini-2.5-flash",
    api_key=os.environ["GEMINI_API_KEY"],
)

openai_agent = create_agent("OpenAIAgent", "Help users.", openai_config)
gemini_agent = create_agent("GeminiAgent", "Help users.", gemini_config)
```

### Model Settings

```python
from agents import Agent, ModelSettings

agent = Agent(
    name="ConfiguredAgent",
    instructions="Help users.",
    model="gpt-4o",
    model_settings=ModelSettings(
        temperature=0.7,
        max_tokens=1000,
        tool_choice="auto",  # "auto", "required", "none", or specific tool
    ),
)
```

### LiteLLM with Reasoning (Gemini)

```python
from agents import Agent, ModelSettings
from agents.extensions.models.litellm_model import LitellmModel
from openai.types.shared import Reasoning

gemini_model = LitellmModel(
    model="gemini/gemini-2.5-pro",
    api_key=os.environ["GEMINI_API_KEY"],
)

agent = Agent(
    name="ReasoningAgent",
    instructions="Think through complex problems step by step.",
    model=gemini_model,
    model_settings=ModelSettings(
        reasoning=Reasoning(effort="medium"),  # "low", "medium", "high"
    ),
)
```

## Fallback Strategy

```python
import asyncio
from agents import Agent, Runner
from agents.extensions.models.litellm_model import LitellmModel

async def run_with_fallback(agent_prompt: str):
    """Try primary model, fall back to secondary on failure."""
    
    primary_agent = Agent(
        name="PrimaryAgent",
        instructions="Help users.",
        model="gpt-4o",
    )
    
    fallback_agent = Agent(
        name="FallbackAgent", 
        instructions="Help users.",
        model=LitellmModel(
            model="gemini/gemini-2.5-flash",
            api_key=os.environ["GEMINI_API_KEY"],
        ),
    )
    
    try:
        result = await Runner.run(primary_agent, agent_prompt)
        return result.final_output
    except Exception as e:
        print(f"Primary failed: {e}, trying fallback...")
        result = await Runner.run(fallback_agent, agent_prompt)
        return result.final_output
```

## Cost Optimization Tips

1. **Use smaller models for simple tasks** - `gpt-4o-mini` or `gemini-2.5-flash`
2. **Cache tool lists** - Reduce API calls with `cache_tools_list=True`
3. **Set max_tokens** - Limit response length when appropriate
4. **Use reasoning only when needed** - `reasoning_effort="low"` for simpler tasks
5. **Batch requests** - Process multiple items in single agent runs