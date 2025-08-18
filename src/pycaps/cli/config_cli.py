import typer
import os

config_app = typer.Typer()

@config_app.command("config", help="Pycaps AI configuration")
def config():
    """Display current AI configuration from environment variables."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("PYCAPS_AI_MODEL", "gpt-4o-mini")
    
    typer.echo("Current AI Configuration:")
    typer.echo(f"  API Key: {'Set' if api_key else 'Not set'}")
    typer.echo(f"  Base URL: {base_url}")
    typer.echo(f"  Model: {model}")
    
    if not api_key:
        typer.echo("\nTo enable AI features, set the following environment variables:")
        typer.echo("  export OPENAI_API_KEY=your_api_key_here")
        typer.echo("  export OPENAI_BASE_URL=https://openrouter.ai/api/v1  # Optional, for compatible APIs")
        typer.echo("  export PYCAPS_AI_MODEL=google/gemini-flash-1.5        # Optional, custom model")
