#!/usr/bin/env python3
"""
Generate animated SVG assets for GitHub profile README.

This script orchestrates data fetching from various APIs and renders
Jinja2 templates into optimized SVGs for the profile.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

# Add script directory to path for imports
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent.parent
TEMPLATE_DIR = ROOT_DIR / "assets" / "templates"
OUTPUT_DIR = ROOT_DIR / "assets" / "generated"

# Import data fetchers
from fetch_wakatime import fetch_wakatime_stats
from fetch_github_activity import fetch_contribution_data


def setup_jinja_env() -> Environment:
    """Create Jinja2 environment with template directory."""
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def generate_terminal_header(env: Environment) -> str:
    """Generate the terminal header SVG."""
    template = env.get_template("terminal-header.svg.j2")

    context = {
        "name": "dinesh",
        "role": "Data Engineer · Full-Stack Builder · AI Tinkerer",
        "bio_line_1": "I build data pipelines by day and ship side projects",
        "bio_line_2": "somewhere between midnight and regret. Based in Toronto.",
        "bio_text": "Data Engineer building things between midnight and regret",
    }

    return template.render(**context)


def generate_social_buttons(env: Environment) -> dict:
    """Generate individual social button SVGs."""
    buttons = {}
    for name in ["linkedin", "email", "portfolio"]:
        template = env.get_template(f"btn-{name}.svg.j2")
        buttons[name] = template.render()
    return buttons


def generate_now_coding(env: Environment) -> str:
    """Generate the WakaTime now-coding SVG."""
    template = env.get_template("now-coding.svg.j2")

    stats = fetch_wakatime_stats()

    context = {
        "status": stats.get("status", "unavailable"),
        "languages": stats.get("languages", []),
        "total_hours": stats.get("total_hours", 0),
    }

    return template.render(**context)


def generate_activity_circuit(env: Environment) -> str:
    """Generate the activity circuit SVG."""
    template = env.get_template("activity-circuit.svg.j2")

    data = fetch_contribution_data()

    context = {
        "status": data.get("status", "unavailable"),
        "total": data.get("total", 0),
        "nodes": data.get("nodes", []),
        "weeks_count": data.get("weeks_count", 0),
    }

    return template.render(**context)


def generate_project_grid(env: Environment) -> str:
    """Generate the project grid SVG."""
    template = env.get_template("project-grid.svg.j2")

    # Project data (could be fetched dynamically in future)
    projects = [
        {
            "name": "Claude Home",
            "icon": "🏠",
            "desc_line1": "Architectural persistence for LLMs.",
            "desc_line2": "Durable filesystem + scheduled execution.",
            "tags": ["Python", "LLM", "AI"],
            "status": "building",
        },
        {
            "name": "PassFX",
            "icon": "🔐",
            "desc_line1": "Zero-knowledge terminal password manager.",
            "desc_line2": "Local-first. Never touches the network.",
            "tags": ["Security", "CLI", "Crypto"],
            "status": "live",
        },
        {
            "name": "Yield",
            "icon": "📊",
            "desc_line1": "Interactive algorithm visualizer.",
            "desc_line2": "Watch data structures move.",
            "tags": ["React", "Education", "Viz"],
            "status": "live",
        },
        {
            "name": "Debate Lab",
            "icon": "⚔️",
            "desc_line1": "AI models in structured debate.",
            "desc_line2": "GPT vs Grok. Claude moderates.",
            "tags": ["AI", "LLM", "Agents"],
            "status": "building",
        },
    ]

    context = {
        "projects": projects,
    }

    return template.render(**context)


def generate_stack_ticker(env: Environment) -> str:
    """Generate the tech stack ticker SVG."""
    template = env.get_template("stack-ticker.svg.j2")

    # 17 technologies from the EPIC
    tech_names = [
        "Python",
        "TypeScript",
        "SQL",
        "PostgreSQL",
        "Snowflake",
        "Kafka",
        "PyTorch",
        "TensorFlow",
        "LangChain",
        "Next.js",
        "React",
        "FastAPI",
        "AWS",
        "Docker",
        "Kubernetes",
        "GitHub Actions",
        "Vercel",
    ]

    # Pre-calculate positions for each technology
    char_width = 9  # Approximate monospace character width
    separator_width = 30  # Width for " // " separator
    padding = 10  # Padding after text

    technologies = []
    x_pos = 0

    for name in tech_names:
        text_width = len(name) * char_width
        sep_x = x_pos + text_width + padding
        technologies.append({
            "name": name,
            "x": x_pos,
            "sep_x": sep_x,
        })
        x_pos = sep_x + separator_width

    half_width = x_pos  # Total width of one copy
    scroll_duration = max(20, half_width // 40)  # ~40px per second

    context = {
        "technologies": technologies,
        "half_width": half_width,
        "scroll_duration": scroll_duration,
    }

    return template.render(**context)


def write_svg(filename: str, content: str) -> None:
    """Write SVG content to output directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / filename

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Generated: {output_path}")


def main() -> int:
    """Main entry point."""
    print(f"Generating SVGs at {datetime.utcnow().isoformat()}Z")
    print(f"Template dir: {TEMPLATE_DIR}")
    print(f"Output dir: {OUTPUT_DIR}")

    env = setup_jinja_env()

    # Generate all SVGs
    try:
        terminal_svg = generate_terminal_header(env)
        write_svg("terminal-header.svg", terminal_svg)

        social_buttons = generate_social_buttons(env)
        for name, svg in social_buttons.items():
            write_svg(f"btn-{name}.svg", svg)

        now_coding_svg = generate_now_coding(env)
        write_svg("now-coding.svg", now_coding_svg)

        activity_circuit_svg = generate_activity_circuit(env)
        write_svg("activity-circuit.svg", activity_circuit_svg)

        project_grid_svg = generate_project_grid(env)
        write_svg("project-grid.svg", project_grid_svg)

        stack_ticker_svg = generate_stack_ticker(env)
        write_svg("stack-ticker.svg", stack_ticker_svg)

        print("All SVGs generated successfully.")
        return 0

    except Exception as e:
        print(f"Error generating SVGs: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
