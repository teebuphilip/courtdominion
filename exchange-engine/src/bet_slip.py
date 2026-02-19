"""Write exchange bet slip output."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import get_today_date, get_timestamp, load_json, write_file, write_json


def run() -> None:
    today = get_today_date()
    sized_path = f"data/sized_bets/{today}.json"

    if not Path(sized_path).exists():
        write_json(f"data/bet_slips/{today}.json", {"bets": []})
        write_file(
            f"data/bet_slips/{today}.md",
            "| Player | Prop | Dir | Proj | Line | Edge% | Conf | Units | Odds | AvailSize | Source | ExecType |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|\n",
        )
        return

    bets = load_json(sized_path)
    output_json_path = f"data/bet_slips/{today}.json"
    write_json(
        output_json_path,
        {
            "date": today,
            "generated_at": get_timestamp(),
            "total_bets": len(bets),
            "bets": bets,
        },
    )

    lines = [
        "| Player | Prop | Dir | Proj | Line | Edge% | Conf | Units | Odds | AvailSize | Source | ExecType |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for bet in bets:
        lines.append(
            f"| {bet['player_name']} | {bet['prop_type']} | {bet['direction']} | {bet['projection']} | "
            f"{bet['line']} | {bet['edge_pct']} | {bet['confidence']} | {bet['units']} | {bet['odds']} | "
            f"{bet['available_size']} | {bet['source']} | {bet['execution_type']} |"
        )

    write_file(f"data/bet_slips/{today}.md", "\n".join(lines) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exchange bet slip")
    parser.parse_args()
    run()
