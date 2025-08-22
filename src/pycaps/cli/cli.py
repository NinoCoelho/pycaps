import typer
from .template_cli import template_app
from .config_cli import config_app
from .render_cli import render_app
from .preview_styles_cli import preview_app

# Get version from pyproject.toml
def get_version():
    try:
        import os
        try:
            import tomllib
        except ImportError:
            tomllib = None
        
        # Try to read from pyproject.toml in development
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        pyproject_path = os.path.join(project_root, "pyproject.toml")
        
        if os.path.exists(pyproject_path):
            if tomllib:
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                    return data.get("project", {}).get("version", "0.3.1")
            else:
                # Fallback for older Python versions
                with open(pyproject_path, "r") as f:
                    for line in f:
                        if line.strip().startswith('version = "'):
                            return line.split('"')[1]
        
        # Try importlib.metadata for installed packages
        import importlib.metadata
        return importlib.metadata.version("pycaps")
    except:
        return "0.3.1"  # Fallback version

app = typer.Typer(
    help="Pycaps, a tool for adding CSS-styled subtitles to videos",
    invoke_without_command=True,
    add_completion=False,
)
app.add_typer(render_app)
app.add_typer(preview_app)
app.add_typer(template_app, name="template")
app.add_typer(config_app)

@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show version and exit")
):
    if version:
        typer.echo(f"pycaps {get_version()}")
        raise typer.Exit()
    
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


