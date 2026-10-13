"""Run the first semantic extraction slice from the repository root."""
import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr

from private_client_graph.models import ExtractionResult
from .semantic import extract_relationships_from_text


def extract_relationships(source_path: Path, *, llm: ChatDeepSeek) -> ExtractionResult:
    """Read one source and invoke the extraction chain once."""
    source = source_path.read_text(encoding="utf-8")
    return extract_relationships_from_text(source, llm=llm)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="deepseek-flash")
    args = parser.parse_args()
    load_dotenv(Path(".env"))
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise SystemExit("DEEPSEEK_API_KEY is not set (add it to .env or the environment)")
    llm = ChatDeepSeek(
        model=args.model,
        api_key=SecretStr(api_key),
        max_retries=0,
        extra_body={"thinking": {"type": "disabled"}},
    )
    result = extract_relationships(Path("cases/case_01/source.txt"), llm=llm)
    output = result.model_dump_json(indent=2)
    run_dir = Path("runs/case_01")
    run_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
    with (run_dir / f"{timestamp}.json").open("x", encoding="utf-8") as run_file:
        run_file.write(output + "\n")
    print(output)
