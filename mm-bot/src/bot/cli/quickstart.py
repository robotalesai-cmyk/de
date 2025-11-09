"""High-level entry point that bootstraps a ready-to-use bot instance."""

from __future__ import annotations

import asyncio
import logging
import shutil
from pathlib import Path

import click
import yaml

from .run_mm import _run
from ..core.config import StrategyConfig

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_TEMPLATE = ROOT_DIR / "configs" / "default.yaml"
DEFAULT_VENUES_TEMPLATE = ROOT_DIR / "configs" / "venues.yaml"
DEFAULT_ENV_TEMPLATE = ROOT_DIR / ".env.example"
USER_STATE_DIR = Path.home() / ".mm-bot"


def _ensure_user_files(config_path: Path) -> Path:
    """Create user-scoped config, venue, and env files if they do not exist."""

    target = config_path.expanduser()
    if target.is_dir():
        target = target / "config.yaml"

    target.parent.mkdir(parents=True, exist_ok=True)
    venues_target = target.parent / "venues.yaml"

    if not target.exists():
        with DEFAULT_CONFIG_TEMPLATE.open("r", encoding="utf-8") as handle:
            contents = handle.read()
        data = yaml.safe_load(contents)
        data["venues_config"] = venues_target.name
        with target.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(data, handle, sort_keys=False)
        click.echo(f"Created strategy config at {target}")
    else:
        click.echo(f"Using existing strategy config at {target}")

    if not venues_target.exists():
        shutil.copy(DEFAULT_VENUES_TEMPLATE, venues_target)
        click.echo(f"Copied venue catalogue to {venues_target}")

    if target.parent == USER_STATE_DIR and DEFAULT_ENV_TEMPLATE.exists():
        env_target = target.parent / ".env"
        if not env_target.exists():
            shutil.copy(DEFAULT_ENV_TEMPLATE, env_target)
            click.echo(f"Created environment template at {env_target}")

    return target


def _install_uvloop() -> None:
    try:
        import uvloop  # type: ignore[import-not-found]

        uvloop.install()
    except ImportError:  # pragma: no cover - optional dependency
        pass


@click.command()
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=USER_STATE_DIR / "config.yaml",
    show_default=True,
    help="Where the generated strategy config will live.",
)
@click.option(
    "--paper/--live",
    default=True,
    help="Run in paper mode (default) or live mode using API keys from the .env file.",
)
@click.option(
    "--init-only",
    is_flag=True,
    help="Generate configuration files and exit without starting the bot.",
)
def main(config_path: Path, paper: bool, init_only: bool) -> None:
    """Bootstrap configuration files and start the bot with sensible defaults."""

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    if not DEFAULT_CONFIG_TEMPLATE.exists() or not DEFAULT_VENUES_TEMPLATE.exists():
        raise FileNotFoundError("Configuration templates are missing from the repository.")

    resolved_config = _ensure_user_files(config_path)
    StrategyConfig.load(resolved_config)  # Validate eagerly so we fail fast on bad edits.

    if init_only:
        click.echo("Configuration initialised. Update API credentials before running live.")
        return

    _install_uvloop()

    mode = "paper" if paper else "live"
    click.echo(f"Starting the market making bot in {mode} mode using {resolved_config}")

    try:
        asyncio.run(_run(resolved_config, paper))
    except KeyboardInterrupt:
        logging.getLogger("bot").info("Shutdown requested by user")


if __name__ == "__main__":
    main()
