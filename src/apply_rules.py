
from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Any


AGENDA_PREFIX_RE = re.compile(r"^(案由[一二三四五六七八九十\d]+)[：:]\s*")
ROC_DATE_RE = re.compile(r"(?P<year>\d{2,3})年(?P<month>\d{1,2})月(?P<day>\d{1,2})日")
URL_RE = re.compile(r"https?://[^\s，。)）]+")


def apply_rules(
    segment: dict[str, Any],
    cleaned_document: dict[str, Any] | None = None,
    segment_index: int | None = None,
) -> dict[str, Any]:
    """
    Convert one segmented agenda item into one normalized pipeline record.

    Args:
        segment: One item returned by segment_document(), shaped like:
            {"title": str, "changes": list[dict]}
        cleaned_document: The cleaned whole-document JSON. Used only for
            source/date/url rules.
        segment_index: Optional stable ordering number from pipeline.py.

    Returns:
        {
            "issue": {...},
            "event": {...}
        }
    """
    if not isinstance(segment, dict):
        raise TypeError("segment must be a dict returned by segment_document().")

    cleaned_document = cleaned_document or {}
    title = str(segment.get("title", "")).strip()
    if not title:
        raise ValueError("segment is missing title.")

    changes = segment.get("changes", [])
    if not isinstance(changes, list):
        changes = []

    document_text = _full_cleaned_text(cleaned_document)
    metadata = cleaned_document.get("metadata", {}) if isinstance(cleaned_document, dict) else {}
    filename_stem = _filename_stem(metadata)

    now = datetime.now().replace(microsecond=0).isoformat()
    meeting_date = _extract_meeting_date(document_text)
    source_defaults = _infer_source_defaults(cleaned_document, document_text)

    issue_id = _stable_id("issue", filename_stem, title)
    event_id = _stable_id("event", filename_stem, title, str(segment_index or ""))

    issue = {
        "issue_id": issue_id,
        "title": _extract_subject(title),
        "topic": "",
        "description": _remove_agenda_prefix(title),
        "cover_summary": "",
        "created_at": now,
        "updated_at": now,
    }

    event = {
        "event_id": event_id,
        "issue_id": issue_id,
        "source_platform": source_defaults["source_platform"],
        "source_organization": source_defaults["source_organization"],
        "source_url": _extract_source_url(document_text),
        "source_authority": source_defaults["source_authority"],
        "content_type": source_defaults["content_type"],
        "content_title": _remove_agenda_prefix(title),
        "content_content": _format_changes(changes),
        "content_summary": "",
        "time_published_at": meeting_date,
        "time_event_at": meeting_date,
        "topic": "",
        "created_at": now,
        "raw_changes": changes,
    }

    return {
        "issue": issue,
        "event": event,
    }


def apply_rules_to_segments(
    segments: list[dict[str, Any]],
    cleaned_document: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Convenience helper for tests or notebooks.
    The real pipeline still calls apply_rules() one segment at a time.
    """
    if not isinstance(segments, list):
        raise TypeError("segments must be a list.")

    return [
        apply_rules(segment, cleaned_document=cleaned_document, segment_index=index)
        for index, segment in enumerate(segments, start=1)
    ]


def _full_cleaned_text(cleaned_document: dict[str, Any]) -> str:
    if not isinstance(cleaned_document, dict):
        return ""

    if cleaned_document.get("text"):
        return str(cleaned_document["text"])

    pages = cleaned_document.get("pages", [])
    if not isinstance(pages, list):
        return ""

    return "\n".join(str(page.get("clean_text", "")) for page in pages if isinstance(page, dict))


def _filename_stem(metadata: dict[str, Any]) -> str:
    filename = str(metadata.get("filename", "")) if isinstance(metadata, dict) else ""
    file_path = str(metadata.get("file_path", "")) if isinstance(metadata, dict) else ""

    if filename:
        return Path(filename).stem
    if file_path:
        return Path(file_path).stem
    return "unknown_source"


def _stable_id(prefix: str, *parts: str, length: int = 12) -> str:
    raw = "|".join(parts)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:length]
    return f"{prefix}_{digest}"


def _roc_to_iso(year: str, month: str, day: str) -> str:
    return f"{int(year) + 1911:04d}-{int(month):02d}-{int(day):02d}"


def _extract_meeting_date(text: str) -> str:
    match = re.search(r"時間[：:]\s*(\d{2,3})年(\d{1,2})月(\d{1,2})日", text)
    if match:
        return _roc_to_iso(*match.groups())

    match = ROC_DATE_RE.search(text)
    if match:
        return _roc_to_iso(match.group("year"), match.group("month"), match.group("day"))

    return ""


def _extract_source_url(text: str) -> str:
    match = URL_RE.search(text)
    return match.group(0) if match else ""


def _infer_source_defaults(cleaned_document: dict[str, Any], document_text: str) -> dict[str, str]:
    metadata = cleaned_document.get("metadata", {}) if isinstance(cleaned_document, dict) else {}
    filename = str(metadata.get("filename", ""))
    file_path = str(metadata.get("file_path", ""))
    hint = f"{filename} {file_path} {document_text[:500]}".lower()

    if "stuaffairs" in hint or "學生輔導委員會" in hint or "學務" in hint:
        return {
            "source_platform": "學務處網站",
            "source_organization": "學務處",
            "source_authority": "官方",
            "content_type": "會議記錄",
        }

    return {
        "source_platform": "",
        "source_organization": "",
        "source_authority": "",
        "content_type": "",
    }


def _remove_agenda_prefix(title: str) -> str:
    return AGENDA_PREFIX_RE.sub("", title).strip()


def _extract_subject(title: str) -> str:
    match = re.search(r"「([^」]+)」", title)
    if match:
        return match.group(1).strip()
    return _remove_agenda_prefix(title)


def _format_changes(changes: list[dict[str, Any]]) -> str:
    blocks: list[str] = []

    for index, change in enumerate(changes, start=1):
        parts = [f"[Change {index}]"]

        revised = change.get("修正條文", "")
        current = change.get("現行條文", "")
        reason = change.get("說明", "")

        if revised:
            parts.append(f"修正條文：\n{revised}")
        if current:
            parts.append(f"現行條文：\n{current}")
        if reason:
            parts.append(f"說明：\n{reason}")

        blocks.append("\n".join(parts))

    return "\n\n".join(blocks)