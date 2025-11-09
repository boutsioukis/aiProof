# AI Student

Autonomous agent for completing course tasks using Claude Agent SDK.

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Copy environment file and add your API key:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

3. Install Claude Code CLI:
```bash
npm install -g @anthropic-ai/claude-code
```

## Run

```bash
ai-student courseX
```

Or use the course-specific runner:
```bash
python courseX/run_agent.py
```

## Course Structure

Each course needs:
- `todo/course_tasks.json` - Task list
- `todo/course_information.json` - Course metadata
- `.claude/CLAUDE.md` - System prompt for the agent
- `knowledge_base/` - Course materials (optional)
