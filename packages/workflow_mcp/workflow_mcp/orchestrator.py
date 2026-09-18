"""Iteration orchestrator: stage gates, attempt budgets, interlock advice."""

from __future__ import annotations

import json
import tomllib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

CONFIG_REL = Path("plans") / "iteration.toml"
LOG_REL = Path("plans") / "iteration_log.jsonl"

VERDICTS = (
    "continue",
    "escalate_upstream",
    "defer",
    "change_success_criteria",
    "ask_human",
)


class Verdict(str, Enum):
    CONTINUE = "continue"
    ESCALATE_UPSTREAM = "escalate_upstream"
    DEFER = "defer"
    CHANGE_SUCCESS_CRITERIA = "change_success_criteria"
    ASK_HUMAN = "ask_human"


@dataclass(frozen=True)
class Stage:
    id: str
    done_when: str = ""
    requires_facts: tuple[str, ...] = ()
    requires_stages: tuple[str, ...] = ()
    done: bool = False


@dataclass(frozen=True)
class Concern:
    id: str
    stage: str
    max_attempts: int = 3
    escalate_to: str = Verdict.CHANGE_SUCCESS_CRITERIA.value
    done_when: str = ""
    reopen: bool = False
    done: bool = False


@dataclass(frozen=True)
class Interlock:
    a: str
    b: str
    blocking: bool = False


@dataclass(frozen=True)
class IterationConfig:
    version: int
    description: str
    facts: dict[str, bool]
    stages: dict[str, Stage]
    concerns: dict[str, Concern]
    interlocks: tuple[Interlock, ...]
    path: Path | None = None

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path) if self.path else None,
            "version": self.version,
            "description": self.description,
            "facts": dict(self.facts),
            "stages": [
                {
                    "id": s.id,
                    "done_when": s.done_when,
                    "requires_facts": list(s.requires_facts),
                    "requires_stages": list(s.requires_stages),
                    "done": s.done,
                }
                for s in self.stages.values()
            ],
            "concerns": [
                {
                    "id": c.id,
                    "stage": c.stage,
                    "max_attempts": c.max_attempts,
                    "escalate_to": c.escalate_to,
                    "done_when": c.done_when,
                    "reopen": c.reopen,
                    "done": c.done,
                }
                for c in self.concerns.values()
            ],
            "interlocks": [
                {"a": i.a, "b": i.b, "blocking": i.blocking} for i in self.interlocks
            ],
        }


@dataclass(frozen=True)
class Attempt:
    concern_id: str
    outcome: str
    note: str = ""
    timestamp: str = ""
    verdict_at_record: str = ""


@dataclass
class Advice:
    concern_id: str
    verdict: str
    reason: str
    blocked_by: list[str] = field(default_factory=list)
    open_interlocks: list[dict[str, Any]] = field(default_factory=list)
    attempts_used: int = 0
    max_attempts: int = 0
    suggested_next: str = ""
    stage_id: str = ""
    svz_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def config_path(project_root: Path) -> Path:
    return Path(project_root) / CONFIG_REL


def log_path(project_root: Path) -> Path:
    return Path(project_root) / LOG_REL


def _as_str_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(x) for x in value)


def _normalize_escalate_to(raw: str) -> str:
    value = (raw or Verdict.CHANGE_SUCCESS_CRITERIA.value).strip()
    if value not in VERDICTS or value == Verdict.CONTINUE.value:
        return Verdict.CHANGE_SUCCESS_CRITERIA.value
    return value


def load_iteration_config(project_root: Path) -> IterationConfig:
    path = config_path(project_root)
    if not path.is_file():
        raise FileNotFoundError(
            f"{CONFIG_REL} not found under {project_root}. "
            "Copy packages/workflow_mcp/examples/iteration.toml or create plans/iteration.toml."
        )
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    meta = raw.get("meta") or {}
    facts_raw = raw.get("facts") or {}
    facts = {str(k): bool(v) for k, v in facts_raw.items()}

    stages: dict[str, Stage] = {}
    for row in raw.get("stages") or []:
        sid = str(row["id"]).strip()
        stages[sid] = Stage(
            id=sid,
            done_when=str(row.get("done_when") or ""),
            requires_facts=_as_str_list(row.get("requires_facts")),
            requires_stages=_as_str_list(row.get("requires_stages")),
            done=bool(row.get("done", False)),
        )

    concerns: dict[str, Concern] = {}
    for row in raw.get("concerns") or []:
        cid = str(row["id"]).strip()
        concerns[cid] = Concern(
            id=cid,
            stage=str(row["stage"]).strip(),
            max_attempts=int(row.get("max_attempts") or 3),
            escalate_to=_normalize_escalate_to(str(row.get("escalate_to") or "")),
            done_when=str(row.get("done_when") or ""),
            reopen=bool(row.get("reopen", False)),
            done=bool(row.get("done", False)),
        )

    interlocks: list[Interlock] = []
    for row in raw.get("interlocks") or []:
        interlocks.append(
            Interlock(
                a=str(row["a"]).strip(),
                b=str(row["b"]).strip(),
                blocking=bool(row.get("blocking", False)),
            )
        )

    return IterationConfig(
        version=int(meta.get("version") or 1),
        description=str(meta.get("description") or ""),
        facts=facts,
        stages=stages,
        concerns=concerns,
        interlocks=tuple(interlocks),
        path=path,
    )


def load_attempt_log(project_root: Path) -> list[Attempt]:
    path = log_path(project_root)
    if not path.is_file():
        return []
    attempts: list[Attempt] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        attempts.append(
            Attempt(
                concern_id=str(data.get("concern_id") or ""),
                outcome=str(data.get("outcome") or ""),
                note=str(data.get("note") or ""),
                timestamp=str(data.get("timestamp") or ""),
                verdict_at_record=str(data.get("verdict_at_record") or ""),
            )
        )
    return attempts


def count_attempts(attempts: list[Attempt], concern_id: str) -> int:
    return sum(1 for a in attempts if a.concern_id == concern_id)


def _stage_facts_ok(stage: Stage, config: IterationConfig) -> bool:
    return all(config.facts.get(f, False) for f in stage.requires_facts)


def _stage_satisfied(stage: Stage, config: IterationConfig) -> bool:
    """A required stage counts only when explicitly marked done."""
    return bool(stage.done)


def _stage_missing_prereqs(
    stage: Stage,
    config: IterationConfig,
) -> list[str]:
    """What blocks working *on* this stage (its own facts + required stages done)."""
    missing: list[str] = []
    for fact in stage.requires_facts:
        if not config.facts.get(fact, False):
            missing.append(f"fact:{fact}")
    for sid in stage.requires_stages:
        nested = config.stages.get(sid)
        if nested is None:
            missing.append(f"stage_missing:{sid}")
        elif not nested.done:
            missing.append(f"stage:{sid}")
    return missing


def _open_interlocks(
    concern_id: str,
    config: IterationConfig,
) -> list[dict[str, Any]]:
    open_list: list[dict[str, Any]] = []
    for link in config.interlocks:
        if concern_id not in (link.a, link.b):
            continue
        partner_id = link.b if link.a == concern_id else link.a
        partner = config.concerns.get(partner_id)
        partner_done = bool(partner.done) if partner else False
        if partner_done:
            continue
        open_list.append(
            {
                "partner": partner_id,
                "blocking": link.blocking,
                "partner_done": partner_done,
            }
        )
    return open_list


def _svz_hint(verdict: str, concern_id: str, reason: str) -> str:
    if verdict not in (
        Verdict.ASK_HUMAN.value,
        Verdict.ESCALATE_UPSTREAM.value,
    ):
        return ""
    safe_reason = reason.replace('"', "'")[:120]
    return (
        f'uv run python scripts/svz.py decision "{concern_id}" '
        f'--context "iteration orchestrator" '
        f'--decision "{verdict}" '
        f'--reason "{safe_reason}"'
    )


def advise(
    project_root: Path,
    concern_id: str,
    *,
    note: str | None = None,
    config: IterationConfig | None = None,
    attempts: list[Attempt] | None = None,
) -> Advice:
    """Return structured verdict for whether to keep iterating on concern_id."""
    cfg = config or load_iteration_config(project_root)
    log = attempts if attempts is not None else load_attempt_log(project_root)
    cid = concern_id.strip()
    concern = cfg.concerns.get(cid)
    if concern is None:
        return Advice(
            concern_id=cid,
            verdict=Verdict.ASK_HUMAN.value,
            reason=f"Unknown concern '{cid}'. Add it to plans/iteration.toml or pick a listed id.",
            suggested_next="get_iteration_config() or edit plans/iteration.toml",
            svz_hint=_svz_hint(
                Verdict.ASK_HUMAN.value,
                cid,
                f"unknown concern {cid}",
            ),
        )

    stage = cfg.stages.get(concern.stage)
    if stage is None:
        return Advice(
            concern_id=cid,
            verdict=Verdict.ASK_HUMAN.value,
            reason=f"Concern '{cid}' references missing stage '{concern.stage}'.",
            stage_id=concern.stage,
            suggested_next="Fix stage id in plans/iteration.toml",
            svz_hint=_svz_hint(
                Verdict.ASK_HUMAN.value,
                cid,
                f"missing stage {concern.stage}",
            ),
        )

    used = count_attempts(log, cid)

    if stage.done and not concern.reopen and not concern.done:
        advice = Advice(
            concern_id=cid,
            verdict=Verdict.ASK_HUMAN.value,
            reason=(
                f"Stage '{stage.id}' is marked done; reopen the concern "
                f"(reopen=true) or unset stage.done before iterating '{cid}'."
            ),
            attempts_used=used,
            max_attempts=concern.max_attempts,
            stage_id=stage.id,
            suggested_next="Set concern.reopen=true or clear stage.done if revisiting",
        )
        advice.svz_hint = _svz_hint(advice.verdict, cid, advice.reason)
        return advice

    if concern.done and not concern.reopen:
        return Advice(
            concern_id=cid,
            verdict=Verdict.ASK_HUMAN.value,
            reason=f"Concern '{cid}' is marked done. Set reopen=true to revisit.",
            attempts_used=used,
            max_attempts=concern.max_attempts,
            stage_id=stage.id,
            suggested_next="Mark reopen=true or pick another concern",
            svz_hint=_svz_hint(
                Verdict.ASK_HUMAN.value,
                cid,
                f"concern {cid} done",
            ),
        )

    blocked = _stage_missing_prereqs(stage, cfg)
    if blocked:
        advice = Advice(
            concern_id=cid,
            verdict=Verdict.ESCALATE_UPSTREAM.value,
            reason=(
                f"Stage '{stage.id}' prerequisites unmet: {', '.join(blocked)}. "
                "Do not keep iterating this concern yet."
            ),
            blocked_by=blocked,
            attempts_used=used,
            max_attempts=concern.max_attempts,
            stage_id=stage.id,
            suggested_next="Satisfy facts/stages upstream, then advise again",
        )
        advice.svz_hint = _svz_hint(advice.verdict, cid, advice.reason)
        return advice

    if used >= concern.max_attempts:
        verdict = concern.escalate_to
        advice = Advice(
            concern_id=cid,
            verdict=verdict,
            reason=(
                f"Attempt budget exhausted ({used}/{concern.max_attempts}) "
                f"for '{cid}'. Escalate per concern.escalate_to={verdict}."
            ),
            attempts_used=used,
            max_attempts=concern.max_attempts,
            stage_id=stage.id,
            suggested_next=(
                "Change success criteria, escalate upstream, or ask human — "
                "do not burn another identical pass"
            ),
        )
        if note:
            advice.reason += f" Last note: {note}"
        advice.svz_hint = _svz_hint(advice.verdict, cid, advice.reason)
        return advice

    open_links = _open_interlocks(cid, cfg)
    blocking = [x for x in open_links if x.get("blocking")]
    if blocking:
        partners = ", ".join(x["partner"] for x in blocking)
        return Advice(
            concern_id=cid,
            verdict=Verdict.DEFER.value,
            reason=(
                f"Blocking interlock(s) open with: {partners}. "
                "Defer or run a paired pass that touches both concerns."
            ),
            open_interlocks=open_links,
            attempts_used=used,
            max_attempts=concern.max_attempts,
            stage_id=stage.id,
            suggested_next=f"Advise/work partner concern(s): {partners}",
        )

    return Advice(
        concern_id=cid,
        verdict=Verdict.CONTINUE.value,
        reason=(
            f"Stage '{stage.id}' gates OK; attempts {used}/{concern.max_attempts}. "
            "One focused pass on this concern is allowed."
        ),
        open_interlocks=open_links,
        attempts_used=used,
        max_attempts=concern.max_attempts,
        stage_id=stage.id,
        suggested_next="Do one pass, then record_iteration_attempt with outcome",
    )


def record_attempt(
    project_root: Path,
    concern_id: str,
    *,
    outcome: str,
    note: str = "",
    verdict_at_record: str = "",
) -> dict[str, Any]:
    """Append one attempt line to plans/iteration_log.jsonl. Does not tick PLAN.md."""
    root = Path(project_root)
    path = log_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not verdict_at_record:
        try:
            verdict_at_record = advise(root, concern_id).verdict
        except FileNotFoundError:
            verdict_at_record = ""
    entry = {
        "concern_id": concern_id.strip(),
        "outcome": outcome.strip(),
        "note": note.strip(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "verdict_at_record": verdict_at_record,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {"success": True, "log_path": str(path), "entry": entry}
