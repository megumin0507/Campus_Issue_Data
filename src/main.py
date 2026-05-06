from pathlib import Path
import argparse

from pipeline import CampusIssuePipeline


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the campus_issue_data pipeline."
    )

    parser.add_argument(
        "--input",
        type=str,
        default="data/raw/stuaffairs/第59次會議紀錄.pdf",
        help="Path to the raw PDF file."
    )

    parser.add_argument(
        "--db",
        type=str,
        default="db/campus_issue.db",
        help="Path to the SQLite database file."
    )

    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Skip semantic extraction using LLM."
    )

    return parser.parse_args()


def main():
    args = parse_args()

    pdf_path = Path(args.input)
    db_path = Path(args.db)

    if not pdf_path.exists():
        raise FileNotFoundError(f"Input PDF not found: {pdf_path}")

    pipeline = CampusIssuePipeline(
        pdf_path=pdf_path,
        db_path=db_path,
        use_llm=not args.skip_llm,
    )

    result = pipeline.run()

    print("\nPipeline finished.")
    print(f"PDF: {pdf_path}")
    print(f"Total segments: {result['total_segments']}")
    print(f"Inserted records: {result['inserted_records']}")
    print(f"Failed records: {result['failed_records']}")


if __name__ == "__main__":
    main()