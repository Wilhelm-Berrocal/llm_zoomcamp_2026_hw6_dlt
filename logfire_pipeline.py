import os
from datetime import UTC, datetime, timedelta

import dlt
from dotenv import load_dotenv
from logfire.query_client import LogfireQueryClient


load_dotenv()

PIPELINE_NAME = 'logfire_pipeline'
DATASET_NAME = 'agent_traces'
DUCKDB_PATH = 'logfire_pipeline.duckdb'
SERVICE_NAME = os.getenv('LOGFIRE_SERVICE_NAME', 'llm-zoomcamp-dlt-homework')


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f'{name} is required in .env')
    return value


@dlt.resource(name='records', write_disposition='replace')
def logfire_records(read_token: str, min_timestamp: datetime, limit: int):
    service_name_sql = SERVICE_NAME.replace("'", "''")
    sql = f"""
    SELECT *
    FROM records
    WHERE service_name = '{service_name_sql}'
    ORDER BY start_timestamp DESC
    """

    with LogfireQueryClient(read_token=read_token) as client:
        result = client.query_json_rows(
            sql=sql,
            min_timestamp=min_timestamp,
            limit=limit,
        )

    rows = result['rows']
    if not rows:
        raise RuntimeError(
            f'No Logfire records found for service_name={SERVICE_NAME!r} '
            f'since {min_timestamp.isoformat()}'
        )

    yield rows


def load(hours: int = 10000, limit: int = 500) -> None:
    read_token = _required_env('LOGFIRE_READ_TOKEN')
    min_timestamp = datetime.now(tz=UTC) - timedelta(hours=hours)

    pipeline = dlt.pipeline(
        pipeline_name=PIPELINE_NAME,
        destination=dlt.destinations.duckdb(DUCKDB_PATH),
        dataset_name=DATASET_NAME,
    )
    info = pipeline.run(logfire_records(read_token, min_timestamp, limit))
    print(info)
    print(pipeline.last_trace.last_normalize_info)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--hours', type=int, default=10000)
    parser.add_argument('--limit', type=int, default=500)
    args = parser.parse_args()

    load(hours=args.hours, limit=args.limit)
