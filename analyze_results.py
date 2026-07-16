import json
import os
from pathlib import Path
from typing import Any

import duckdb
from dotenv import load_dotenv


DUCKDB_PATH = 'logfire_pipeline.duckdb'
SCHEMA = 'agent_traces'
RECORDS_TABLE = f'"{SCHEMA}"."records"'
load_dotenv()

SERVICE_NAME = os.getenv('LOGFIRE_SERVICE_NAME', 'llm-zoomcamp-dlt-homework')


def _load_json(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _find_input_tokens(value: Any) -> list[int]:
    value = _load_json(value)
    found: list[int] = []

    if isinstance(value, dict):
        for key, item in value.items():
            if key == 'gen_ai.usage.input_tokens':
                try:
                    found.append(int(item))
                except (TypeError, ValueError):
                    pass
            found.extend(_find_input_tokens(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_find_input_tokens(item))

    return found


def _row_input_tokens(row: dict[str, Any]) -> int:
    tokens: list[int] = []

    for column, value in row.items():
        normalized = column.replace('__', '.').replace('_', '.')
        if value is None:
            continue
        if normalized.endswith('gen.ai.usage.input.tokens'):
            try:
                tokens.append(int(value))
            except (TypeError, ValueError):
                pass

    attributes = row.get('attributes')
    if attributes:
        tokens.extend(_find_input_tokens(attributes))

    # A model-call span should only have one input-token value, but de-duping
    # protects against counting both a flattened column and the raw JSON field.
    return sum(set(tokens))


def _range_answer(total_tokens: int) -> str:
    ranges = [
        (100, 500, '100 - 500'),
        (1500, 5000, '1500 - 5000'),
        (10000, 20000, '10000 - 20000'),
        (50000, 100000, '50000 - 100000'),
    ]
    for lower, upper, label in ranges:
        if lower <= total_tokens <= upper:
            return label
    return f'outside listed ranges ({total_tokens})'


def _q1_submit_choice(span_count: int) -> str:
    choices = [1, 5, 15, 30]
    return str(min(choices, key=lambda choice: abs(choice - span_count)))


def main() -> None:
    if not Path(DUCKDB_PATH).exists():
        raise RuntimeError(f'{DUCKDB_PATH} does not exist; run logfire_pipeline.py first')

    con = duckdb.connect(DUCKDB_PATH)

    table_count = con.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = ?
        """,
        [SCHEMA],
    ).fetchone()[0]

    trace_id = con.execute(
        f"""
        SELECT trace_id
        FROM {RECORDS_TABLE}
        WHERE service_name = ?
        GROUP BY trace_id
        ORDER BY MAX(start_timestamp) DESC
        LIMIT 1
        """,
        [SERVICE_NAME],
    ).fetchone()[0]

    rows = con.execute(
        f"""
        SELECT *
        FROM {RECORDS_TABLE}
        WHERE trace_id = ?
        ORDER BY start_timestamp
        """,
        [trace_id],
    ).fetchall()
    columns = [desc[0] for desc in con.description]
    records = [dict(zip(columns, row)) for row in rows]

    span_count = sum(1 for row in records if row.get('kind') == 'span')
    input_tokens = sum(_row_input_tokens(row) for row in records if row.get('kind') == 'span')

    print(f'trace_id={trace_id}')
    print(f'q1_span_count={span_count}')
    print(f'q1_submit_choice={_q1_submit_choice(span_count)}')
    print(f'q2_table_count={table_count}')
    print(f'q3_input_tokens={input_tokens}')
    print(f'q3_answer={_range_answer(input_tokens)}')

    print('\nspan_names:')
    for row in records:
        if row.get('kind') == 'span':
            print(f"- {row.get('span_name')}: {row.get('message')}")


if __name__ == '__main__':
    main()
