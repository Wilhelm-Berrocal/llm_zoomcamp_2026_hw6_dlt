import os
from datetime import UTC, datetime

import logfire
from dotenv import load_dotenv

load_dotenv()

SERVICE_NAME = os.getenv('LOGFIRE_SERVICE_NAME', 'llm-zoomcamp-dlt-homework')

logfire.configure(
    service_name=SERVICE_NAME,
    environment='homework',
    send_to_logfire='if-token-present',
)
logfire.instrument_pydantic_ai()

from agent import faq_agent, SearchDeps
from ingest import build_index, load_faq_data


QUESTION = 'How do I run Ollama locally?'


def main():
    print(f'run_started_at={datetime.now(tz=UTC).isoformat()}')
    print(f'logfire_service_name={SERVICE_NAME}')
    print(f'question={QUESTION}')

    # Download the FAQ and build the search index
    documents = load_faq_data()
    index = build_index(documents)

    # Inject the index into the agent via the dependency container
    deps = SearchDeps(index=index)

    # Ask a question. run_sync blocks until the agent is done;
    # the agent may call search multiple times before answering.
    result = faq_agent.run_sync(QUESTION, deps=deps)

    print(result.output)
    logfire.force_flush()


if __name__ == '__main__':
    main()
