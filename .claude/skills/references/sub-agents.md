# Sub-Agents and Multi-Agent Patterns

Patterns for building multi-agent systems with the OpenAI Agents SDK.

## Pattern 1: Agents as Tools

Use specialized agents as tools for a main orchestrator agent:

```python
from agents import Agent, Runner, function_tool

# Specialist agents
booking_agent = Agent(
    name="BookingAgent",
    instructions="Handle booking requests. Confirm details before finalizing.",
)

refund_agent = Agent(
    name="RefundAgent", 
    instructions="Process refund requests. Verify eligibility first.",
)

# Main orchestrator with agents as tools
customer_agent = Agent(
    name="CustomerService",
    instructions=(
        "Handle customer inquiries. "
        "Use booking_expert for reservations. "
        "Use refund_expert for refund requests."
    ),
    tools=[
        booking_agent.as_tool(
            tool_name="booking_expert",
            tool_description="Handles booking questions and requests.",
        ),
        refund_agent.as_tool(
            tool_name="refund_expert",
            tool_description="Handles refund questions and requests.",
        ),
    ],
)
```

## Pattern 2: Handoffs

Transfer control completely to another agent:

```python
from agents import Agent

# Specialist agents
math_tutor = Agent(
    name="MathTutor",
    handoff_description="Specialist for math questions",
    instructions="Help with math problems. Show step-by-step solutions.",
)

history_tutor = Agent(
    name="HistoryTutor",
    handoff_description="Specialist for history questions",
    instructions="Help with historical queries. Provide context and dates.",
)

# Triage agent that hands off to specialists
triage_agent = Agent(
    name="TriageAgent",
    instructions=(
        "Determine the user's question type. "
        "Hand off to math_tutor for math questions. "
        "Hand off to history_tutor for history questions."
    ),
    handoffs=[math_tutor, history_tutor],
)
```

## Pattern 3: Dynamic Instructions

Customize agent behavior based on context:

```python
from dataclasses import dataclass
from agents import Agent, RunContextWrapper

@dataclass
class UserContext:
    name: str
    user_id: str
    is_premium: bool
    preferences: dict

def dynamic_instructions(
    context: RunContextWrapper[UserContext],
    agent: Agent[UserContext]
) -> str:
    user = context.context
    base = f"You are helping {user.name}. "
    
    if user.is_premium:
        base += "Provide detailed, premium-level support. "
    else:
        base += "Provide standard support. "
    
    if user.preferences.get("formal"):
        base += "Use formal language."
    
    return base

agent = Agent[UserContext](
    name="ContextualAgent",
    instructions=dynamic_instructions,
)
```

## Pattern 4: Structured Output Agents

Return typed data from agents:

```python
from pydantic import BaseModel
from agents import Agent

class TaskAnalysis(BaseModel):
    task_type: str
    priority: int
    estimated_time: str
    required_tools: list[str]

analyzer_agent = Agent(
    name="TaskAnalyzer",
    instructions="Analyze tasks and return structured analysis.",
    output_type=TaskAnalysis,
)

# Usage
result = await Runner.run(analyzer_agent, "Schedule a meeting with the team")
analysis: TaskAnalysis = result.final_output
print(f"Priority: {analysis.priority}")
```

## Pattern 5: Hierarchical Multi-Agent

Build complex agent hierarchies:

```python
from agents import Agent

# Level 2: Specialists
code_reviewer = Agent(
    name="CodeReviewer",
    instructions="Review code for quality and best practices.",
)

security_auditor = Agent(
    name="SecurityAuditor", 
    instructions="Check code for security vulnerabilities.",
)

# Level 1: Team leads
backend_lead = Agent(
    name="BackendLead",
    instructions="Coordinate backend development tasks.",
    tools=[
        code_reviewer.as_tool("code_review", "Review code quality"),
        security_auditor.as_tool("security_audit", "Audit security"),
    ],
)

frontend_lead = Agent(
    name="FrontendLead",
    instructions="Coordinate frontend development tasks.",
)

# Level 0: Project manager
project_manager = Agent(
    name="ProjectManager",
    instructions=(
        "Manage development projects. "
        "Delegate backend tasks to backend_lead. "
        "Delegate frontend tasks to frontend_lead."
    ),
    handoffs=[backend_lead, frontend_lead],
)
```

## Pattern 6: Agent with Guardrails

Add input/output validation:

```python
from agents import (
    Agent, 
    InputGuardrail, 
    OutputGuardrail,
    GuardrailFunctionOutput,
    Runner,
)
from pydantic import BaseModel

class ContentCheck(BaseModel):
    is_appropriate: bool
    reason: str

# Guardrail agent
content_checker = Agent(
    name="ContentChecker",
    instructions="Check if content is appropriate for all ages.",
    output_type=ContentCheck,
)

async def check_input(
    ctx, agent, input_data
) -> GuardrailFunctionOutput:
    result = await Runner.run(content_checker, input_data)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not result.final_output.is_appropriate,
    )

main_agent = Agent(
    name="SafeAgent",
    instructions="Help users with their requests.",
    input_guardrails=[
        InputGuardrail(guardrail_function=check_input),
    ],
)
```

## When to Use Each Pattern

| Pattern | Use Case |
|---------|----------|
| Agents as Tools | Main agent needs specialized capabilities but stays in control |
| Handoffs | Complete delegation to specialist, user talks directly to specialist |
| Dynamic Instructions | Personalized behavior based on user/session context |
| Structured Output | Need typed, validated responses for downstream processing |
| Hierarchical | Complex organizations with multiple management levels |
| Guardrails | Production systems requiring input/output validation |