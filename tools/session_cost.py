"""Tokens, wall-clock time and API-price cost estimate of one Claude Code session.

Usage:
  python -I session_cost.py SESSION.jsonl [--json OUT.json]
  python -I session_cost.py --latest PROJECT_DIR      # newest *.jsonl in a project folder
  (transcripts live in ~/.claude/projects/<cwd with / replaced by ->/<session-uuid>.jsonl;
   e.g. a session started in /path/to/project -> ~/.claude/projects/-path-to-project/)

What it counts:
- Every API response once. Claude Code writes one JSONL line per content block, all carrying the
  same message.id and the same usage, so lines are de-duplicated by message.id.
- Subagent transcripts in <session-uuid>/subagents/*.jsonl are included (listed separately).
- Tokens: input (uncached), cache writes (5 min / 1 h TTL), cache reads, output (thinking included).
- Time: first real user prompt (not a tool result) -> last assistant response. Also active time
  (sum of gaps between consecutive events, capping idle gaps at 10 min) to spot pauses.
- Effort and model as recorded on each assistant line (to verify the run used the intended effort).

Cost = what these tokens would cost at public Claude API list prices (standard speed). A Claude Max
subscription does not bill per token; this is an "at API prices" estimate for the video.
Prices (USD per million tokens), Claude Opus 5.5, from the claude-api skill (cached 2026-10-06):
input 4.00, output 20.00, cache read 0.20 (0.05x), cache write 5 min 5.00 (1.25x), 1 h 8.00 (2x).
"""
import sys, json, glob, os, argparse, collections
from datetime import datetime

PRICES = {  # USD per 1M tokens
    "claude-opus-5-5": {"input": 4.00, "output": 20.00, "cache_read": 0.20, "write_5m": 5.00, "write_1h": 8.00},
    # Claude Fable 5.2 (claude-api skill, cached 2026-11-03): input 8, output 40, cache read 0.20;
    # cache writes at the standard multipliers of the input price (5 min 1.25x, 1 h 2x).
    "claude-fable-5-2": {"input": 8.00, "output": 40.00, "cache_read": 0.20, "write_5m": 10.00, "write_1h": 16.00},
}
IDLE_CAP_S = 600


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def is_real_prompt(d):
    """A user line typed/sent as a prompt, not a tool_result echo."""
    if d.get("type") != "user" or d.get("isSidechain"):
        return False
    c = d.get("message", {}).get("content")
    if isinstance(c, str):
        return True
    return isinstance(c, list) and any(b.get("type") == "text" for b in c) and not any(b.get("type") == "tool_result" for b in c)


def read(path):
    msgs, events, prompts = {}, [], []
    meta = collections.Counter()
    for line in open(path, encoding="utf-8"):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = d.get("timestamp")
        if t and d.get("type") in ("user", "assistant"):
            events.append(ts(t))
        if is_real_prompt(d) and t:
            prompts.append(ts(t))
        if d.get("type") == "assistant":
            m = d.get("message", {})
            mid = m.get("id") or d.get("uuid")
            if mid not in msgs:
                msgs[mid] = {"usage": m.get("usage") or {}, "model": m.get("model"), "t": ts(t) if t else None, "effort": d.get("effort")}
                meta[(m.get("model"), d.get("effort"))] += 1
    return msgs, sorted(events), sorted(prompts), meta


def tokens(msgs):
    tot = collections.Counter()
    for m in msgs.values():
        u = m["usage"]
        cc = u.get("cache_creation") or {}
        w1h = cc.get("ephemeral_1h_input_tokens", 0) or 0
        w5m = cc.get("ephemeral_5m_input_tokens", 0) or 0
        if not cc:  # older transcripts: no TTL breakdown -> assume 5 min
            w5m = u.get("cache_creation_input_tokens", 0) or 0
        tot["input"] += u.get("input_tokens", 0) or 0
        tot["output"] += u.get("output_tokens", 0) or 0
        tot["thinking"] += (u.get("output_tokens_details") or {}).get("thinking_tokens", 0) or 0
        tot["cache_read"] += u.get("cache_read_input_tokens", 0) or 0
        tot["write_5m"] += w5m
        tot["write_1h"] += w1h
        tot["web_search"] += (u.get("server_tool_use") or {}).get("web_search_requests", 0) or 0
    tot["responses"] = len(msgs)
    return tot


def cost(tok, model):
    p = PRICES.get(model)
    if not p:
        return None
    return sum(tok[k] * p[k] for k in ("input", "output", "cache_read", "write_5m", "write_1h")) / 1e6


def cut(part, since):
    """Keep only responses/events at or after `since` (prompt timestamp)."""
    msgs, ev, pr, meta = part
    if since is None:
        return part
    msgs = {k: v for k, v in msgs.items() if v["t"] and v["t"] >= since}
    meta = collections.Counter()
    for v in msgs.values():
        meta[(v["model"], v.get("effort"))] += 1
    return msgs, [e for e in ev if e >= since], [q for q in pr if q >= since], meta


def first_prompt_matching(path, text):
    """Timestamp of the first real user prompt whose text contains `text` (e.g. the cross-session task)."""
    for line in open(path, encoding="utf-8"):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not is_real_prompt(d) or not d.get("timestamp"):
            continue
        c = d.get("message", {}).get("content")
        s = c if isinstance(c, str) else " ".join(b.get("text", "") for b in c if b.get("type") == "text")
        if text in s:
            return ts(d["timestamp"])
    sys.exit(f"no user prompt containing {text!r} in {path}")


def analyse(path, from_prompt=1, from_match=None):
    main = read(path)
    since = None
    if from_match:
        since = first_prompt_matching(path, from_match)
    elif from_prompt > 1:
        if len(main[2]) < from_prompt:
            sys.exit(f"only {len(main[2])} user prompt(s) in {path}; cannot start at prompt {from_prompt}")
        since = main[2][from_prompt - 1]
    main = cut(main, since)
    subs = sorted(glob.glob(os.path.join(path[:-6], "subagents", "*.jsonl")))
    parts = [("main", path, main)] + [("subagent " + os.path.basename(s), s, cut(read(s), since)) for s in subs]
    out = {"session": path, "parts": [], "total": {}}
    total = collections.Counter()
    total_cost = 0.0
    models = collections.Counter()
    for name, p, (msgs, ev, pr, meta) in parts:
        tok = tokens(msgs)
        c = 0.0
        for model in {m["model"] for m in msgs.values()}:
            sub = {k: v for k, v in msgs.items() if v["model"] == model}
            cm = cost(tokens(sub), model)
            if cm is None:
                print(f"WARNING: no price for model {model} in {name}; cost excludes it", file=sys.stderr)
            else:
                c += cm
        total.update(tok)
        total_cost += c
        models.update(meta)
        out["parts"].append({"name": name, "tokens": dict(tok), "cost_usd": round(c, 4),
                             "model_effort": {f"{m}/{e}": n for (m, e), n in meta.items()}})
    msgs, ev, pr, _ = main
    first = pr[0] if pr else (ev[0] if ev else None)
    last = max((m["t"] for m in msgs.values() if m["t"]), default=None)
    active = 0.0
    for a, b in zip(ev, ev[1:]):
        active += min((b - a).total_seconds(), IDLE_CAP_S)
    out["total"] = {
        "tokens": dict(total),
        "tokens_all_input": total["input"] + total["cache_read"] + total["write_5m"] + total["write_1h"],
        "cost_usd_at_api_prices": round(total_cost, 2),
        "start": first.astimezone().isoformat(timespec="seconds") if first else None,  # local time
        "end": last.astimezone().isoformat(timespec="seconds") if last else None,
        "wall_clock_min": round((last - first).total_seconds() / 60, 1) if first and last else None,
        "active_min_idle_capped": round(active / 60, 1),
        "user_prompts": len(pr),
        "model_effort": {f"{m}/{e}": n for (m, e), n in models.items()},
    }
    return out


def show(r):
    t = r["total"]
    k = t["tokens"]
    print(f"session: {r['session']}")
    print(f"  model/effort lines : {t['model_effort']}")
    print(f"  time               : {t['start']} -> {t['end']}  = {t['wall_clock_min']} min "
          f"(active, idle gaps capped at 10 min: {t['active_min_idle_capped']} min); user prompts: {t['user_prompts']}")
    print(f"  responses          : {k.get('responses', 0)}")
    print(f"  input uncached     : {k.get('input', 0):,}")
    print(f"  cache writes 5m/1h : {k.get('write_5m', 0):,} / {k.get('write_1h', 0):,}")
    print(f"  cache reads        : {k.get('cache_read', 0):,}")
    print(f"  output (thinking)  : {k.get('output', 0):,} ({k.get('thinking', 0):,})")
    print(f"  all input tokens   : {t['tokens_all_input']:,}")
    print(f"  cost at API prices : ${t['cost_usd_at_api_prices']:.2f}")
    if len(r["parts"]) > 1:
        for p in r["parts"]:
            print(f"    - {p['name']}: ${p['cost_usd']:.2f}, {p['tokens'].get('responses', 0)} responses")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("session", nargs="?")
    ap.add_argument("--latest", help="project dir under ~/.claude/projects; use its newest *.jsonl")
    ap.add_argument("--json", help="also write the result as JSON")
    ap.add_argument("--from-prompt", type=int, default=1,
                    help="measure from the N-th user prompt on (e.g. 2 when prompt 1 was a 'wait' placeholder)")
    ap.add_argument("--from-match", help="measure from the first user prompt containing this text (overrides --from-prompt)")
    a = ap.parse_args()
    path = a.session
    if a.latest:
        files = glob.glob(os.path.join(os.path.expanduser(a.latest), "*.jsonl"))
        if not files:
            sys.exit(f"no *.jsonl in {a.latest}")
        path = max(files, key=os.path.getmtime)
    if not path:
        ap.error("give SESSION.jsonl or --latest PROJECT_DIR")
    res = analyse(path, a.from_prompt, a.from_match)
    show(res)
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1, default=str)
