import json
from pipeline import build_graph

# This file runs a full example of the LangGraph pipeline
# using mock user input and explicit calendar confirmation.


def main() -> None:
    # Compile and run the graph with mock inputs.
    app = build_graph().compile()
    result = app.invoke(
        {
            "user_profile": {
                "medical_history": [
                    "History of knee pain",
                    "Mild asthma",
                ],
                "short_term_goals": ["Improve cardio fitness"],
                "long_term_goals": ["Complete a 10K run"],
                "availability": [
                    {
                        "date": "2026-02-11",
                        "start_time": "18:00",
                        "end_time": "19:00",
                    },
                    {
                        "date": "2026-02-13",
                        "start_time": "18:00",
                        "end_time": "19:00",
                    },
                    {
                        "date": "2026-02-15",
                        "start_time": "09:00",
                        "end_time": "10:00",
                    },
                ],
            },
            "user_confirmation": True,
        }
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    # Execute example run.
    main()
