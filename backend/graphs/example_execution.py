from __future__ import annotations

import json

from backend.graphs.graph import create_first_graph, create_initial_state


def run_example() -> None:
    graph = create_first_graph()

    initial_state = create_initial_state("What is happening with TCS?")
    # LangGraph compiled graph is runnable; support both invoke and async run patterns
    result = graph.invoke(initial_state)

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    run_example()
