from pathlib import Path
import json
from datetime import datetime

from extract_pdf import extract_pdf
from clean_text import clean_text
from segment_document import segment_document
from apply_rules import apply_rules
from semantic_extract import semantic_extract
from validate_record import validate_record
from insert_db import insert_record


class CampusIssuePipeline:
    """
    Controls the full workflow:

    raw PDF
    -> extracted text
    -> cleaned text
    -> segmented issue items
    -> rule-based normalized records
    -> LLM-enriched records
    -> validation
    -> database insertion
    """

    def __init__(self, pdf_path: Path, db_path: Path, use_llm: bool = True):
        self.pdf_path = Path(pdf_path)
        self.db_path = Path(db_path)
        self.use_llm = use_llm

        self.project_root = Path.cwd()

        self.extracted_dir = self.project_root / "data" / "extracted"
        self.segmented_dir = self.project_root / "data" / "segmented"
        self.normalized_dir = self.project_root / "data" / "normalized"
        self.enriched_dir = self.project_root / "data" / "enriched"
        self.failed_dir = self.project_root / "data" / "failed"

        self._ensure_dirs()

    def _ensure_dirs(self):
        for path in [
            self.extracted_dir,
            self.segmented_dir,
            self.normalized_dir,
            self.enriched_dir,
            self.failed_dir,
            self.db_path.parent,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def run(self) -> dict:
        print("Starting campus_issue_data pipeline...")

        extracted = self._run_extraction()
        cleaned_text = self._run_cleaning(extracted)
        segments = self._run_segmentation(cleaned_text, extracted)

        inserted_count = 0
        failed_count = 0

        for index, segment in enumerate(segments, start=1):
            try:
                print(f"\nProcessing segment {index}/{len(segments)}")

                normalized_record = self._run_rule_extraction(segment, index)

                if self.use_llm:
                    enriched_record = self._run_semantic_extraction(
                        normalized_record,
                        index,
                    )
                else:
                    enriched_record = normalized_record

                self._run_validation(enriched_record)

                self._run_db_insertion(enriched_record)

                inserted_count += 1

            except Exception as error:
                failed_count += 1
                self._save_failed_record(
                    segment=segment,
                    index=index,
                    error=error,
                )

        return {
            "total_segments": len(segments),
            "inserted_records": inserted_count,
            "failed_records": failed_count,
        }

    def _run_extraction(self) -> dict:
        print("Step 1: extracting PDF...")

        extracted = extract_pdf(self.pdf_path)

        output_path = self.extracted_dir / f"{self.pdf_path.stem}.json"
        self._save_json(output_path, extracted)

        return extracted

    def _run_cleaning(self, extracted: dict) -> str:
        print("Step 2: cleaning text...")

        raw_text = extracted["text"]
        cleaned_text = clean_text(raw_text)

        output_path = self.extracted_dir / f"{self.pdf_path.stem}_cleaned.txt"
        output_path.write_text(cleaned_text, encoding="utf-8")

        return cleaned_text

    def _run_segmentation(self, cleaned_text: str, extracted: dict) -> list[dict]:
        print("Step 3: segmenting document...")

        segments = segment_document(
            text=cleaned_text,
            metadata=extracted.get("metadata", {}),
        )

        output_path = self.segmented_dir / f"{self.pdf_path.stem}_segments.json"
        self._save_json(output_path, segments)

        return segments

    def _run_rule_extraction(self, segment: dict, index: int) -> dict:
        print("Step 4: applying rule-based extraction...")

        normalized_record = apply_rules(segment)

        output_path = self.normalized_dir / f"{self.pdf_path.stem}_record_{index}.json"
        self._save_json(output_path, normalized_record)

        return normalized_record

    def _run_semantic_extraction(self, record: dict, index: int) -> dict:
        print("Step 5: applying semantic extraction...")

        enriched_record = semantic_extract(record)

        output_path = self.enriched_dir / f"{self.pdf_path.stem}_record_{index}.json"
        self._save_json(output_path, enriched_record)

        return enriched_record

    def _run_validation(self, record: dict):
        print("Step 6: validating record...")

        validation_result = validate_record(record)

        if validation_result is True:
            return

        if isinstance(validation_result, tuple):
            is_valid, errors = validation_result
            if not is_valid:
                raise ValueError(f"Validation failed: {errors}")
            return

        if validation_result is None:
            return

        raise ValueError(f"Unexpected validation result: {validation_result}")

    def _run_db_insertion(self, record: dict):
        print("Step 7: inserting record into database...")

        insert_record(
            db_path=self.db_path,
            record=record,
        )

    def _save_failed_record(self, segment: dict, index: int, error: Exception):
        print(f"Segment {index} failed: {error}")

        failed_record = {
            "pdf": str(self.pdf_path),
            "segment_index": index,
            "error": str(error),
            "failed_at": datetime.now().isoformat(timespec="seconds"),
            "segment": segment,
        }

        output_path = self.failed_dir / f"{self.pdf_path.stem}_failed_{index}.json"
        self._save_json(output_path, failed_record)

    def _save_json(self, path: Path, data):
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )