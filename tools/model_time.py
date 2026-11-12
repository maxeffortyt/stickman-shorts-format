"""How long the model itself was working in a Claude Code session, vs time spent in local tools.

usage: python -I model_time.py SESSION.jsonl --from-match TEXT [--update COST.json]
- model time  = for every API response: (last line of that response) - (the user/tool-result line just before it)
                (thinking + writing + API latency; remote, so barely affected by a busy laptop)
- tool time   = for every tool call: (its tool_result line) - (the line with its tool_use)
                (local work: renders, scripts, installs; a busy laptop makes this longer)
- wall time   = first prompt matching TEXT -> last assistant line
Background tasks return at once, so their work is in neither number (it shows up as idle time).
With --update, writes total.model_working_min / tool_time_min / wall_min into an existing session_cost JSON.
"""
import sys, json, argparse
from datetime import datetime


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session")
    ap.add_argument("--from-match", required=True)
    ap.add_argument("--update")
    a = ap.parse_args()
    lines = []
    for line in open(a.session, encoding="utf-8"):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("isSidechain") or d.get("type") not in ("user", "assistant") or not d.get("timestamp"):
            continue
        lines.append(d)
    # start = first user prompt containing the text
    start = None
    for d in lines:
        if d["type"] == "user":
            c = d.get("message", {}).get("content")
            s = c if isinstance(c, str) else " ".join(b.get("text", "") for b in (c or []) if isinstance(b, dict) and b.get("type") == "text")
            if a.from_match in s:
                start = ts(d["timestamp"]); break
    if start is None:
        sys.exit("start prompt not found")
    lines = [d for d in lines if ts(d["timestamp"]) >= start]
    model_s, tool_s = 0.0, 0.0
    last_user = None
    cur_id, cur_first_prev, cur_last = None, None, None
    tool_start = {}
    def close():
        nonlocal model_s
        if cur_id and cur_first_prev and cur_last:
            model_s += max(0.0, (cur_last - cur_first_prev).total_seconds())
    for d in lines:
        t = ts(d["timestamp"])
        if d["type"] == "assistant":
            mid = d.get("message", {}).get("id")
            if mid != cur_id:
                close()
                cur_id, cur_first_prev, cur_last = mid, last_user or t, t
            else:
                cur_last = t
            for b in d.get("message", {}).get("content", []) or []:
                if b.get("type") == "tool_use":
                    tool_start[b.get("id")] = t
        else:
            c = d.get("message", {}).get("content")
            if isinstance(c, list):
                for b in c:
                    if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") in tool_start:
                        tool_s += max(0.0, (t - tool_start.pop(b["tool_use_id"])).total_seconds())
            last_user = t
    close()
    last_assistant = max(ts(d["timestamp"]) for d in lines if d["type"] == "assistant")
    wall = (last_assistant - start).total_seconds()
    res = {"model_working_min": round(model_s / 60, 1), "tool_time_min": round(tool_s / 60, 1), "wall_min": round(wall / 60, 1),
           "start": start.isoformat(), "end": last_assistant.isoformat()}
    print(json.dumps(res))
    if a.update:
        j = json.load(open(a.update))
        j.setdefault("total", {}).update(res)
        json.dump(j, open(a.update, "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
