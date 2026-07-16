# LLM Zoomcamp 2026 dlt Homework

Source homework:
`/home/guermo/Documents/llm-zoomcamp/cohorts/2026/workshops/dlt/homework.md`

## Verified Run

The homework was run end-to-end with:

```bash
uv sync --cache-dir .uv-cache
uv run --cache-dir .uv-cache python main.py
uv run --cache-dir .uv-cache python logfire_pipeline.py --hours 10000 --limit 500
uv run --cache-dir .uv-cache python analyze_results.py
```

Trace loaded from Logfire:

```text
trace_id=019f68aa0cdeb5a34fbb5bd899a74a69
q1_span_count=4
q1_submit_choice=5
q2_table_count=24
q3_input_tokens=1628
q3_answer=1500 - 5000
```

Q1 note: the actual trace contains 4 span rows:

- `invoke_agent faq_agent`
- `chat gpt-5.4-mini`
- `execute_tool search`
- `chat gpt-5.4-mini`

The homework form does not list `4`, so the closest listed option is `5`.

## Submit

| Question | Answer |
| --- | --- |
| Q1 | `5` |
| Q2 | `24` |
| Q3 | `1500 - 5000` |

Submit at:
https://courses.datatalks.club/llm-zoomcamp-2026/homework/dlt
