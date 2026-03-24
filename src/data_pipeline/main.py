from __future__ import annotations

import argparse

from data_pipeline.logger import init_logger
from data_pipeline.orchestrator import run_pipeline
from data_pipeline.settings import load_settings


def cli() -> None:
    parser = argparse.ArgumentParser(prog="clinical-pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="Execute pipeline")
    run_cmd.add_argument("--config", default="configs/pipeline.yaml")
    run_cmd.add_argument("--stage", default=None)
    run_cmd.add_argument("--verbose", action="store_true")

    args = parser.parse_args()
    if args.command == "run":
        _, env = load_settings(args.config)
        logger = init_logger("cli", "DEBUG" if args.verbose else env.log_level)
        summary = run_pipeline(args.config, stage=args.stage, verbose=args.verbose)
        logger.info("Pipeline completed: %s", summary)


if __name__ == "__main__":
    cli()
