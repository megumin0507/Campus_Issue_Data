
import re


def extract_titles(pages: list[dict]) -> list[str]:
    text = "\n".join(
        page["clean_text"]
        for page in pages
        if not page["is_table_page"]
    )

    pattern = r"(案由[一二三四五六七八九十]+：.*?)(?=\n?說明：)"
    return re.findall(pattern, text, re.S)


def split_rows(table_text: str) -> list[str]:
    rows = re.split(r"\[Table Row \d+\]", table_text)
    return [row.strip() for row in rows if row.strip()]


def get_field(row: str, field_name: str) -> str:
    pattern = rf"{field_name}:\s*(.*?)(?=\n修正條文:|\n現行條文:|\n說明:|$)"
    match = re.search(pattern, row, re.S)

    if match:
        return match.group(1).strip()

    return ""


def parse_row(row: str) -> dict:
    return {
        "修正條文": get_field(row, "修正條文"),
        "現行條文": get_field(row, "現行條文"),
        "說明": get_field(row, "說明"),
    }


def should_start_new_change(change: dict) -> bool:
    revised = change["修正條文"]
    current = change["現行條文"]

    if revised.startswith("第"):
        return True

    if current.startswith("第"):
        return True

    return False


def append_or_merge_change(changes: list[dict], change: dict) -> None:
    if not changes:
        changes.append(change)
        return

    if should_start_new_change(change):
        changes.append(change)
        return

    previous = changes[-1]

    for key in ["修正條文", "現行條文", "說明"]:
        if change[key]:
            if previous[key]:
                previous[key] += "\n" + change[key]
            else:
                previous[key] = change[key]


def segment_document(cleaned_document: dict) -> list[dict]:
    pages = cleaned_document["pages"]
    titles = extract_titles(pages)

    segments = []
    current_segment = dict()
    title_index = -1
    previous_is_table_page = False

    for page in pages:
        is_table_page = page["is_table_page"]

        # false -> true means a new amendment table starts
        if is_table_page and not previous_is_table_page:
            title_index += 1

            current_segment = {
                "title": titles[title_index] if title_index < len(titles) else "",
                "changes": [],
            }

            segments.append(current_segment)

        if is_table_page:
            rows = split_rows(page["clean_text"])

            for row in rows:
                change = parse_row(row)

                if not any(change.values()):
                    continue
                
                append_or_merge_change(current_segment["changes"], change)
                
        previous_is_table_page = is_table_page

    return segments