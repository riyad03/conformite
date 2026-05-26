#!/usr/bin/env python
"""CLI entry point.

Usage:
    # Analyse
    python main.py analyse "Ouverture de compte (régionalisation)"
    python main.py analyse "Procedure A" "Procedure B"

    # Start REST API server
    python main.py serve
    python main.py serve --port 8080 --reload
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import os
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"]    = "false"


def _cmd_analyse(args) -> None:
    from module_folder.config import AppConfig
    from module_folder.data.repository import ProcedureResolver
    from module_folder.pipeline.runner import run_batch, run_pipeline_for_titles

    config   = AppConfig()
    resolver = ProcedureResolver(config.procedures_dir)
    paths    = resolver.resolve(args.procedures)

    if not paths:
        print("[ERR] Aucune procédure trouvée. Vérifiez les titres et PROCEDURES_DIR.", file=sys.stderr)
        sys.exit(1)

    if len(paths) == 1:
        rapport = run_pipeline_for_titles(
            procedure_path=paths[0],
            selected_processes=args.procedures,
            config=config,
        )
        print(f"\nScore : {rapport.score_global}/100 ({rapport.niveau_global})")
        print(f"Concernes : {rapport.nb_concernes} | Conformes : {rapport.nb_conformes} | NC : {rapport.nb_non_conformes}")
    else:
        rapports = run_batch(
            procedure_paths=paths,
            selected_processes=args.procedures,
            config=config,
        )
        global_rapport = rapports.get("__global__")
        if global_rapport:
            print(f"\nRapport global : rapports/rapport_global.html")
            print(f"Score global   : {global_rapport.score_global}/100 ({global_rapport.niveau_global})")


def _cmd_serve(args) -> None:
    import uvicorn

    uvicorn.run(
        "module_folder.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="GRC Conformité CLI")
    sub = parser.add_subparsers(dest="command")

    # analyse subcommand
    p_analyse = sub.add_parser("analyse", help="Analyse une ou plusieurs procédures.")
    p_analyse.add_argument("procedures", nargs="+", metavar="TITRE")

    # serve subcommand
    p_serve = sub.add_parser("serve", help="Lance le serveur REST API.")
    p_serve.add_argument("--host",   default="0.0.0.0")
    p_serve.add_argument("--port",   type=int, default=8000)
    p_serve.add_argument("--reload", action="store_true")

    args = parser.parse_args()

    if args.command == "analyse":
        _cmd_analyse(args)
    elif args.command == "serve":
        _cmd_serve(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
