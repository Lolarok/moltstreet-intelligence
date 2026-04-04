#!/usr/bin/env python3
"""
MoltStreet Intelligence — AI Analysis Agent
Uses DeepAgents to analyze scan results and produce market insights.

Usage:
    python3 src/agent.py                          # Analyze latest scan
    python3 src/agent.py --data data/scan.json    # Analyze specific file
    python3 src/agent.py --output analysis.json   # Custom output path

Requires: deepagents, OPENAI_API_KEY (or compatible LLM provider)
"""
import sys
import os
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_scan_data(data_path: str = None) -> dict:
    """Load scan results from JSON file or generate fresh."""
    if data_path and os.path.exists(data_path):
        with open(data_path) as f:
            return json.load(f)

    # If no data file, import and run the scanner directly
    from src.main import run_scan
    from src.config import ALERT_THRESHOLD

    results = run_scan(top=100)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "projects": results,
    }


def build_analysis_prompt(scan_data: dict) -> str:
    """Build the agent prompt from scan data."""
    projects = scan_data.get("projects", [])
    generated_at = scan_data.get("generated_at", "unknown")

    # Summarize top performers and alerts
    alerts = [p for p in projects if p.get("score", 0) >= 65]
    strong_buys = [p for p in projects if p.get("score", 0) >= 78]

    # Format projects for the prompt
    project_summary = []
    for p in projects[:30]:  # Top 30 to keep prompt manageable
        signals_str = ", ".join(p.get("signals", [])[:4])
        project_summary.append(
            f"- {p['symbol']} (score: {p['score']}, rating: {p.get('rating', '?')}, "
            f"price: ${p.get('price', 0):.4f}, 7d: {p.get('p7', 0):+.1f}%, "
            f"sector: {p.get('category', '?')}, "
            f"signals: {signals_str or 'none'})"
        )

    return f"""You are a crypto market analyst. Analyze these scan results from MoltStreet Intelligence.

Scan time: {generated_at}
Total projects scanned: {len(projects)}
Active alerts (score ≥ 65): {len(alerts)}
Strong buys (score ≥ 78): {len(strong_buys)}

TOP 30 PROJECTS BY SCORE:
{chr(10).join(project_summary)}

Provide a structured analysis with:

1. **market_overview** (2-3 sentences): What's the overall market sentiment based on these scores?

2. **top_picks** (list): Top 3-5 projects to watch RIGHT NOW with brief reasoning.

3. **emerging_signals** (list): Any interesting patterns? (e.g., AI sector heating up, L2s undervalued, specific momentum plays)

4. **risk_flags** (list): What looks overheated or risky?

5. **sector_themes** (object): Key themes per sector (e.g., {"ai": "Strong momentum, watch TAO", "perp": "HYPE dominant"})

Write your response as a JSON object with these exact keys. Keep insights concise and actionable."""


def run_agent_analysis(scan_data: dict) -> dict:
    """Run the DeepAgents analysis. Returns structured analysis."""
    try:
        from deepagents import create_deep_agent
    except ImportError:
        return {
            "error": "deepagents not installed. Run: pip install deepagents",
            "market_overview": "Analysis unavailable — deepagents package not found.",
            "top_picks": [],
            "emerging_signals": [],
            "risk_flags": ["DeepAgents not installed"],
            "sector_themes": {},
        }

    prompt = build_analysis_prompt(scan_data)

    agent = create_deep_agent(
        system_prompt=(
            "You are a crypto market analyst specializing in DeFi, L1/L2 ecosystems, "
            "and emerging crypto sectors. You analyze quantitative scoring data and "
            "provide concise, actionable insights. Always respond with valid JSON."
        ),
    )

    result = agent.invoke({
        "messages": [{"role": "user", "content": prompt}]
    })

    # Extract the agent's final response
    messages = result.get("messages", [])
    if messages:
        last_msg = messages[-1]
        content = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)

        # Try to parse as JSON
        try:
            # Strip markdown code blocks if present
            cleaned = content.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:cleaned.rfind("```")]
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "market_overview": content[:500],
                "top_picks": [],
                "emerging_signals": [],
                "risk_flags": [],
                "sector_themes": {},
            }

    return {
        "market_overview": "Agent produced no output.",
        "top_picks": [],
        "emerging_signals": [],
        "risk_flags": [],
        "sector_themes": {},
    }


def generate_analysis(scan_data: dict, output_path: str = None) -> dict:
    """Full pipeline: scan → analyze → save."""
    print("🧠 Running AI market analysis...")

    analysis = run_agent_analysis(scan_data)

    # Add metadata
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scan_time": scan_data.get("generated_at"),
        "projects_analyzed": len(scan_data.get("projects", [])),
        "analysis": analysis,
    }

    if output_path:
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)
        print(f"📊 Analysis saved → {output_path}")

    return output


def main():
    parser = argparse.ArgumentParser(description="MoltStreet AI Analyst")
    parser.add_argument("--data", type=str, help="Path to scan JSON data")
    parser.add_argument("--output", type=str, default=None, help="Output path for analysis JSON")
    args = parser.parse_args()

    # Default output next to moltstreet-intelligence dashboard
    if not args.output:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        args.output = os.path.join(base, "dashboard", "analysis.json")

    scan_data = load_scan_data(args.data)
    generate_analysis(scan_data, args.output)


if __name__ == "__main__":
    main()
