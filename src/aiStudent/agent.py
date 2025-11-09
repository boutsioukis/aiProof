#!/usr/bin/env python3
"""
Autonomous agent for completing course tasks using Claude SDK.

This agent operates autonomously, making its own decisions about:
- Task order and priority
- Output locations
- Status updates
- Task approach and execution
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

import anyio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    CLIConnectionError,
    ResultMessage,
    TextBlock,
)


def load_course_data(course_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load course tasks and course information JSON files."""
    todo_dir = course_path / "todo"
    
    tasks_file = todo_dir / "course_tasks.json"
    info_file = todo_dir / "course_information.json"
    
    if not tasks_file.exists():
        raise FileNotFoundError(f"Tasks file not found: {tasks_file}")
    if not info_file.exists():
        raise FileNotFoundError(f"Course info file not found: {info_file}")
    
    with open(tasks_file, "r", encoding="utf-8") as f:
        tasks_data = json.load(f)
    
    with open(info_file, "r", encoding="utf-8") as f:
        course_info = json.load(f)
    
    return tasks_data, course_info


def construct_autonomous_instruction(
    tasks_data: dict[str, Any], course_info: dict[str, Any]
) -> str:
    """Construct the initial instruction prompt for Claude."""
    
    course_name = course_info.get("course_name", "Unknown Course")
    total_tasks = len(tasks_data.get("tasks", []))
    pending_tasks = [
        t for t in tasks_data.get("tasks", []) if t.get("status") == "pending"
    ]
    
    prompt = f"""I need you to autonomously complete all course tasks for {course_name}.

You have access to:
- Course information and context
- Knowledge base materials in knowledge_base/ folder
- All task details in todo/course_tasks.json

There are {total_tasks} total tasks, with {len(pending_tasks)} currently pending.

Please begin working autonomously:
1. Review all tasks and decide on your approach
2. Start with the first task
3. Use the knowledge base as needed
4. Complete each task fully before moving to the next
5. Update task status in course_tasks.json as you progress
6. Save outputs to appropriate locations

Work independently and make your own decisions. Begin now."""
    
    return prompt


def find_claude_cli() -> Optional[str]:
    """Find Claude CLI path for the current platform."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            npm_cli = Path(appdata) / "npm" / "claude.cmd"
            if npm_cli.exists():
                return str(npm_cli)
    # For Unix-like systems, assume 'claude' is in PATH
    return None


async def run_autonomous_agent(course_path: Path):
    """
    Run the autonomous agent to complete course tasks.
    
    Args:
        course_path: Path to the course directory containing todo/ and knowledge_base/
    """
    course_path = course_path.resolve()
    knowledge_base_path = course_path / "knowledge_base"
    
    print(f"AI Student - Autonomous Agent")
    print(f"Course directory: {course_path}")
    print(f"Knowledge base: {knowledge_base_path}")
    print("-" * 60)
    
    # Validate course directory structure
    if not course_path.exists():
        raise FileNotFoundError(f"Course directory not found: {course_path}")
    
    # Load course data
    try:
        print("Loading course data...")
        tasks_data, course_info = load_course_data(course_path)
        print(f"Loaded {len(tasks_data.get('tasks', []))} tasks")
        print(f"Course: {course_info.get('course_name', 'Unknown')}")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Configure Claude SDK options
    # Claude Code will read system prompt from .claude/CLAUDE.md via setting_sources=["project"]
    cli_path = find_claude_cli()
    
    options = ClaudeAgentOptions(
        cwd=str(course_path),
        system_prompt=None,  # Use .claude/CLAUDE.md via setting_sources
        allowed_tools=["Read", "Write", "Bash", "Skill"],
        permission_mode="acceptEdits",
        add_dirs=[str(knowledge_base_path)] if knowledge_base_path.exists() else [],
        setting_sources=["project"],  # Required to load .claude/CLAUDE.md
        cli_path=cli_path,
    )
    
    # Initialize cost tracking
    total_cost = 0.0
    message_count = 0
    
    print("\nConnecting to Claude SDK...")
    print("Starting autonomous task completion...")
    print("-" * 60)
    
    try:
        async with ClaudeSDKClient(options=options) as client:
            # Give Claude full context and autonomy
            initial_prompt = construct_autonomous_instruction(tasks_data, course_info)
            print("\nSending initial instruction to Claude...")
            await client.query(initial_prompt)
            
            # Let Claude work autonomously, track costs and messages
            print("\nClaude is now working autonomously...")
            print("(You can monitor progress below)\n")
            
            async for msg in client.receive_messages():
                message_count += 1
                
                # Display assistant messages
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            # Print first 200 chars of each text block
                            text = block.text
                            if len(text) > 200:
                                print(f"Claude: {text[:200]}...")
                            else:
                                print(f"Claude: {text}")
                
                # Track costs
                elif isinstance(msg, ResultMessage):
                    if msg.total_cost_usd:
                        cost = msg.total_cost_usd
                        total_cost += cost
                        print(f"\n[Cost for this response: ${cost:.6f}]")
                        print(f"[Cumulative total: ${total_cost:.6f}]\n")
            
            print("\n" + "=" * 60)
            print("Agent session completed")
            print(f"Total messages processed: {message_count}")
            print(f"Total cost: ${total_cost:.6f}")
            print("=" * 60)
    
    except CLIConnectionError as e:
        print(f"\nConnection error: {e}", file=sys.stderr)
        print("Make sure Claude Code CLI is installed and ANTHROPIC_API_KEY is set.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        print(f"Cost so far: ${total_cost:.6f}")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


class AutonomousAgent:
    """Autonomous agent class for completing course tasks."""
    
    def __init__(self, course_path: Path):
        """
        Initialize the autonomous agent.
        
        Args:
            course_path: Path to the course directory
        """
        self.course_path = Path(course_path).resolve()
    
    async def run(self):
        """Run the autonomous agent."""
        await run_autonomous_agent(self.course_path)


def main():
    """Main entry point for CLI usage."""
    if len(sys.argv) < 2:
        print("Usage: ai-student <course_directory>", file=sys.stderr)
        print("Example: ai-student courseX", file=sys.stderr)
        sys.exit(1)
    
    course_path = Path(sys.argv[1]).resolve()
    anyio.run(run_autonomous_agent, course_path)


if __name__ == "__main__":
    main()

