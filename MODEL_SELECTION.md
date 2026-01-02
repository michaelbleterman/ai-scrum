# Model Selection Guide

## Overview

The AI Sprint Framework uses different Gemini models for different agent types to optimize both **performance** and **cost**. Each agent is assigned a model based on its computational complexity and reasoning requirements.

## Model Assignments

| Agent Role | Model | Rationale |
|------------|-------|-----------|
| **Orchestrator** | `gemini-2.5-pro` | Requires advanced reasoning for workflow coordination, dependency resolution, and reactive decision-making |
| **QA Engineer** | `gemini-2.5-pro` | Needs deep code analysis and comprehensive reasoning for test generation and defect detection |
| **Backend Developer** | `gemini-2.5-flash` | Best price-performance for coding tasks; balanced capabilities for API and database work |
| **Frontend Developer** | `gemini-2.5-flash` | Well-rounded model handles UI code generation and design implementation efficiently |
| **DevOps Engineer** | `gemini-2.5-flash` | Balanced performance for infrastructure code and automation tasks |
| **Security Engineer** | `gemini-2.5-flash` | Good systematic code analysis and vulnerability pattern detection |
| **Product Manager** | `gemini-2.5-flash` | Quality research and requirement definition capabilities at excellent price-performance |

## Available Models

### Gemini 2.5 Pro
- **Best for**: Complex reasoning, code analysis, large datasets, long context
- **Pricing**: $1.25/1M input tokens, $10/1M output tokens (≤200K context)
- **Use cases**: Orchestration, comprehensive testing, deep analysis

### Gemini 2.5 Flash
- **Best for**: Large-scale processing, agentic tasks, balanced performance
- **Pricing**: $0.10/1M input tokens, $0.40/1M output tokens
- **Use cases**: Development tasks, documentation, balanced reasoning

### Gemini 2.5 Flash-Lite
- **Best for**: High throughput, cost-efficiency, simple tasks
- **Pricing**: $0.10/1M input tokens, $0.40/1M output tokens
- **Use cases**: Summarization, classification, high-volume requests

## Environment Variable Overrides

You can override the default model for any agent type using environment variables in your `.env` file:

```bash
# Override specific agent models
MODEL_ORCHESTRATOR=gemini-3-pro          # Upgrade orchestrator to latest model
MODEL_QA=gemini-2.5-flash                # Downgrade QA to save costs
MODEL_BACKEND=gemini-3-flash             # Use latest for backend
MODEL_FRONTEND=gemini-2.5-flash-lite     # Use lite for simple UI work
MODEL_DEVOPS=gemini-2.5-flash
MODEL_SECURITY=gemini-2.5-flash
MODEL_PM=gemini-2.5-pro                  # Upgrade PM for better research

# Global fallback (used if no specific override matches)
MODEL_NAME=gemini-2.5-flash
```

## Cost Optimization

### Estimated Costs Per Sprint

Assuming a typical sprint with 10 tasks:

**Optimized Setup** (current):
- Orchestrator (2.5 Pro): 50K tokens × $5.00/1M = $0.25
- QA (2.5 Pro): 40K tokens × $5.00/1M = $0.20
- 4 Developers (2.5 Flash): 120K tokens × $0.25/1M = $0.03
- PM (2.5 Flash): 20K tokens × $0.25/1M = $0.005
- **Total**: ~$0.49 per sprint

**All Pro Setup** (maximum quality):
- All agents using 2.5 Pro: 230K tokens × $5.00/1M = $1.15
- **Total**: ~$1.15 per sprint (+135% cost)

**All Flash-Lite Setup** (minimum cost):
- All agents using 2.5 Flash-Lite: 230K tokens × $0.25/1M = $0.06
- **Total**: ~$0.06 per sprint (-88% cost)
- ⚠️ **Warning**: May compromise quality on complex tasks

### Recommendations

1. **Default setup** (current): Best balance of performance and cost
2. **High-stakes projects**: Upgrade all to Pro models via environment variables
3. **Budget-constrained**: Keep orchestrator/QA on Pro, downgrade others to Flash-Lite
4. **Experimentation**: Use Flash-Lite initially, upgrade as needed

## How It Works

The model selection happens automatically in `sprint_config.py`:

1. **Check for explicit override**: `MODEL_{AGENT_NAME}` environment variable
2. **Use role mapping**: Predefined mapping based on agent complexity
3. **Fallback to global default**: `MODEL_NAME` if no match found

Example:
```python
# In your code
agent = agent_factory(
    name="backend_worker_1",
    instruction="...",
    tools=worker_tools,
    agent_role="Backend"  # Automatically selects gemini-2.5-flash
)
```

## Monitoring Usage

Track your model usage in:
- **Google Cloud Console**: View API calls and costs
- **Sprint Debug Log**: Check `sprint_debug.log` for agent creation messages showing assigned models
- **Cost Analysis**: Compare actual costs against estimates after 5-10 sprints

## Best Practices

1. **Start with defaults**: The current setup is optimized for most use cases
2. **Monitor performance**: Track quality vs. cost over multiple sprints
3. **Adjust selectively**: Only override when you see clear benefits
4. **Document changes**: Note why you changed defaults in your project README
5. **Review regularly**: Model capabilities and pricing evolve; revisit quarterly

## Troubleshooting

### Agent using wrong model
- Check environment variables in `.env`
- Verify agent role is passed correctly to `agent_factory()`
- Review `sprint_debug.log` for model selection messages

### Unexpected costs
- Verify model names are correct (typos default to `MODEL_NAME`)
- Check for accidental Pro model usage on high-volume agents
- Monitor token usage in Google Cloud Console

### Poor performance
- Consider upgrading specific agents to Pro models
- Check if agent is getting appropriate model for its complexity
- Review task complexity vs. model capabilities
