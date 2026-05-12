import re
from typing import Any


def clean_text(raw_text: str) -> str:
    """
    Clean plain extracted text from a PDF.

    This function is used for normal paragraph text.
    It removes common PDF extraction noise while keeping useful structure.
    """

    if raw_text is None:
        return ""

    text = raw_text

    # Normalize newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove excessive spaces
    text = re.sub(r"[ \t]+", "", text)

    # Remove repeated empty lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove common page markers like "1 / 3"
    text = re.sub(r"\n?\s*\d+\s*/\s*\d+\s*\n?", "\n", text)

    # Remove standalone page numbers
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)

    # Fix broken Chinese line breaks
    text = merge_broken_chinese_lines(text)

    # Clean again after merging
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def merge_broken_chinese_lines(text: str) -> str:
    """
    Merge lines that are probably broken by PDF extraction.

    Example:
        國立臺灣大學學生事務規章研修小
        組組織辦法

    becomes:
        國立臺灣大學學生事務規章研修小組組織辦法

    But it tries to preserve structural lines like:
        案由一：
        說 明：
        決 議：
        第一條
        一、
        二、
    """

    lines = text.split("\n")
    merged_lines: list[str] = []

    for line in lines:
        line = line.strip()

        if not line:
            merged_lines.append("")
            continue

        if not merged_lines:
            merged_lines.append(line)
            continue

        previous = merged_lines[-1]

        if should_merge_lines(previous, line):
            merged_lines[-1] = previous + line
        else:
            merged_lines.append(line)

    return "\n".join(merged_lines)


def should_merge_lines(previous: str, current: str) -> bool:
    """
    Decide whether two lines should be merged.

    This is heuristic-based, not perfect.
    """

    if not previous or not current:
        return False

    # Do not merge after sentence-ending punctuation
    if previous.endswith(("。", "：", ":", "；", ";", "！", "？", "」", "）", ")")):
        return False

    # Merge if previous and current are mostly Chinese text
    if ends_with_chinese(previous) and starts_with_chinese(current):
        return True

    return False


def starts_with_chinese(text: str) -> bool:
    return bool(re.match(r"^[\u4e00-\u9fff]", text))


def ends_with_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]$", text))


def clean_table(table: list[list[Any]]) -> list[list[str]]:
    """
    Clean a table extracted by pdfplumber.

    Input example:
        [
            ["修正條文", "現行條文", "說明"],
            ["第一條 ...", "第一條 ...", "一、..."]
        ]

    Output:
        Same table, but cells are cleaned strings.
    """

    cleaned_table: list[list[str]] = []

    for row in table:
        cleaned_row = []

        for cell in row:
            if cell is None:
                cleaned_cell = ""
            else:
                cleaned_cell = clean_text(str(cell))

            cleaned_row.append(cleaned_cell)

        # Skip fully empty rows
        if any(cell.strip() for cell in cleaned_row):
            cleaned_table.append(cleaned_row)

    return cleaned_table


def table_to_text(table: list[list[Any]]) -> str:
    """
    Convert extracted table into LLM-friendly text.

    This version does NOT assume the first row is a header.
    It treats columns by position:

    col 0 -> 修正條文
    col 1 -> 現行條文
    col 2 -> 說明

    It also skips header-like rows such as:
    修正條文 | 現行條文 | 說明
    """

    cleaned_table = clean_table(table)

    if not cleaned_table:
        return ""

    column_names = ["修正條文", "現行條文", "說明"]

    output_blocks = []
    row_number = 1

    for row in cleaned_table:
        if is_table_header_row(row):
            continue

        if is_empty_row(row):
            continue

        block_lines = [f"[Table Row {row_number}]"]

        for col_index, cell in enumerate(row):
            cell = cell.strip()

            if not cell:
                continue

            column_name = column_names[col_index]

            block_lines.append(f"{column_name}: {cell}")

        if len(block_lines) > 1:
            output_blocks.append("\n".join(block_lines))
            row_number += 1

    return "\n\n".join(output_blocks)


def is_empty_row(row: list[str]) -> bool:
    return not any(cell.strip() for cell in row)


def is_table_header_row(row: list[str]) -> bool:
    """
    Detect rows that are only table headers.
    """

    header_keywords = {"修 正 條 文", "現 行 條 文", "說 明", "修正條文", "現行條文", "說明"}
    non_empty_cells = [cell for cell in row if cell]

    if non_empty_cells and all(cell in header_keywords for cell in non_empty_cells):
        return True

    return False


def clean_extracted_document(extracted: dict) -> dict:
    """
    Clean the full extracted document.

    For each page:
    - if the page has no valid table, clean normal text
    - if the page has valid tables, convert tables into column-based text

    Output:
        {
            "metadata": {...},
            "pages": [
                {
                    "page_number": 1,
                    "is_table_page": false,
                    "clean_text": "..."
                }
            ],
            "text": "full cleaned document text"
        }
    """

    cleaned_pages = []

    for page in extracted.get("pages", []):
        page_number = page.get("page_number")
        page_text = page.get("text", "")
        tables = page.get("tables", [])

        is_table_page = bool(tables)

        if is_table_page:
            table_texts = []

            for table in tables:
                converted = table_to_text(table)
                if converted.strip():
                    table_texts.append(converted)

            clean_page_text = "\n\n".join(table_texts).strip()

        else:
            clean_page_text = clean_text(page_text)

        cleaned_pages.append(
            {
                "page_number": page_number,
                "is_table_page": is_table_page,
                "clean_text": clean_page_text,
            }
        )

    full_text = "\n\n".join(
        page["clean_text"]
        for page in cleaned_pages
        if page["clean_text"].strip()
    )

    return {
        "metadata": extracted.get("metadata", {}),
        "pages": cleaned_pages,
        "text": full_text,
    }