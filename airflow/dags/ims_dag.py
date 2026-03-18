import os
import sys
import smtplib
from datetime import datetime, date, timedelta
import json
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pendulum
from dotenv import load_dotenv
from uuid import NAMESPACE_URL, uuid5

# Setup project paths
PROJECT_ROOT = "/home/prabhu/Institution Management System"
IMS_APP_DIR = os.path.join(PROJECT_ROOT, "app")
IMS_ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(IMS_ENV_PATH)
log_path = os.path.join(PROJECT_ROOT, "logs", "etl.log")

# Add paths to sys.path for imports
for _p in [IMS_APP_DIR, PROJECT_ROOT]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Setup logging
def log_etl(msg: str):
    now = pendulum.now("Asia/Kolkata").strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a") as f:
        f.write(f"[{now} IST] [IMS_DAG_ETL] {msg}\n")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from database import MYSQL_SessionLocal, PG_SessionLocal

# DAG configuration
ALERT_FROM_EMAIL = os.getenv("from_email")
ALERT_TO_EMAIL = os.getenv("to_email")
ALERT_SMTP_HOST = os.getenv("ALERT_SMTP_HOST") or os.getenv("SMTP_HOST")
ALERT_SMTP_PORT = os.getenv("ALERT_SMTP_PORT") or os.getenv("SMTP_PORT")
ALERT_SMTP_USERNAME = os.getenv("ALERT_SMTP_USERNAME") or os.getenv("SMTP_USERNAME") or ALERT_FROM_EMAIL
ALERT_SMTP_PASSWORD = os.getenv("ALERT_SMTP_PASSWORD") or os.getenv("SMTP_PASSWORD")
ALERT_SMTP_STARTTLS = (os.getenv("ALERT_SMTP_STARTTLS") or os.getenv("SMTP_STARTTLS") or "true").lower() == "true"
ALERT_SMTP_SSL = (os.getenv("ALERT_SMTP_SSL") or os.getenv("SMTP_SSL") or "false").lower() == "true"

# Airflow webserver base URL — used to build clickable task log links in alert emails.
# Resolution order: env var AIRFLOW_WEBSERVER_BASE_URL → airflow.cfg [webserver] base_url → localhost fallback.
def _get_webserver_base_url() -> str:
    env_val = os.getenv("AIRFLOW_WEBSERVER_BASE_URL", "").rstrip("/")
    if env_val:
        return env_val
    try:
        from airflow.configuration import conf
        return conf.get("webserver", "base_url", fallback="http://localhost:8080").rstrip("/")
    except Exception:
        return "http://localhost:8080"

AIRFLOW_WEBSERVER_BASE_URL = _get_webserver_base_url()

def _build_log_url(
    dag_id: str,
    task_id: str,
    run_id: str = "",
    try_number: object = None,
    task_instance=None,
) -> str:
    """Return a clickable Airflow log URL for a task.

    Prefers the URL already stored on the task_instance object (populated by
    Airflow's own webserver), but falls back to building one from parts so that
    inferred / early-callback tasks still get a usable link.
    """
    # Use the attribute Airflow sets when a real TI is available.
    if task_instance is not None:
        raw = getattr(task_instance, "log_url", None) or ""
        if raw:
            return raw

    if not dag_id or not task_id:
        return ""

    base = AIRFLOW_WEBSERVER_BASE_URL
    if run_id:
        # Airflow 2.x grid view — deep-links directly to the log tab.
        encoded_run_id = run_id.replace("+", "%2B").replace(":", "%3A")
        url = (
            f"{base}/dags/{dag_id}/grid"
            f"?dag_run_id={encoded_run_id}&task_id={task_id}&tab=logs"
        )
        if try_number not in (None, "unknown", ""):
            url += f"&try_number={try_number}"
        return url

    # Fallback: classic log view (works on all 2.x versions).
    return f"{base}/log?dag_id={dag_id}&task_id={task_id}"

OPENLINEAGE_NAMESPACE = os.getenv("OPENLINEAGE_NAMESPACE", "ims.airflow")
OPENLINEAGE_PRODUCER = os.getenv(
    "OPENLINEAGE_PRODUCER",
    "ims.airflow.error-lineage",
)
PIPELINE_TASK_IDS = [
    "gen_daily_attendance",
    "generate_salary",
    "stage_golden_source",
    "create_golden_snapshot",
    "etl_dimensions",
    "etl_facts",
    "teacher_performance",
    "finalize_golden_batch",
]

default_args = {
    "owner": "prabhu",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

def _format_metrics_html(metrics: dict) -> str:
    if not metrics:
        return "<p>No task metrics were available for this run.</p>"

    rows = []
    for task_id, payload in metrics.items():
        rows.append(
            "<tr>"
            f"<td>{task_id}</td>"
            f"<td><pre>{json.dumps(payload, indent=2, default=str)}</pre></td>"
            "</tr>"
        )

    return (
        "<table border='1' cellspacing='0' cellpadding='6'>"
        "<tr><th>Task</th><th>Returned Metrics</th></tr>"
        + "".join(rows)
        + "</table>"
    )

def _collect_run_metrics(context: dict) -> dict:
    ti = context.get("ti")
    metrics = {}
    if ti is None:
        return metrics

    for task_id in PIPELINE_TASK_IDS:
        value = ti.xcom_pull(task_ids=task_id, key="return_value")
        if value is not None:
            metrics[task_id] = value
    return metrics

def _query_task_instances_from_db(dag_run) -> list:
    if dag_run is None:
        return []

    try:
        from airflow.models.taskinstance import TaskInstance
        from airflow.utils.session import create_session
    except Exception:
        return []

    dag_id = getattr(dag_run, "dag_id", None)
    run_id = getattr(dag_run, "run_id", None)
    logical_date = getattr(dag_run, "logical_date", None) or getattr(dag_run, "execution_date", None)
    if not dag_id:
        return []

    try:
        with create_session() as session:
            query = session.query(TaskInstance).filter(TaskInstance.dag_id == dag_id)
            if hasattr(TaskInstance, "run_id") and run_id:
                query = query.filter(TaskInstance.run_id == run_id)
            elif logical_date is not None:
                execution_col = getattr(TaskInstance, "execution_date", None)
                if execution_col is not None:
                    query = query.filter(execution_col == logical_date)
            return query.all()
    except Exception as exc:
        log_etl(f"[openlineage] Failed to query task instances from Airflow metadata DB: {exc}")
        return []

def _get_task_instances(dag_run, context_task_instance=None) -> list:
    task_instances = []
    if dag_run is not None:
        getter = getattr(dag_run, "get_task_instances", None)
        if callable(getter):
            try:
                task_instances = getter() or []
            except Exception:
                task_instances = []

        if not task_instances:
            task_instances = getattr(dag_run, "task_instances", []) or []

        if not task_instances:
            task_instances = _query_task_instances_from_db(dag_run)

    task_map = {
        getattr(task_instance, "task_id", None): task_instance
        for task_instance in task_instances
        if getattr(task_instance, "task_id", None)
    }

    if context_task_instance is not None and getattr(context_task_instance, "task_id", None):
        task_map[getattr(context_task_instance, "task_id")] = context_task_instance

    return list(task_map.values())

def _collect_task_states(dag_run, context_task_instance=None) -> list[str]:
    task_instances = _get_task_instances(dag_run, context_task_instance)

    state_by_task_id = {
        getattr(task_instance, "task_id", None): getattr(task_instance, "state", "unknown")
        for task_instance in task_instances
        if getattr(task_instance, "task_id", None)
    }

    return [
        f"<li>{task_id}: {state_by_task_id[task_id]}</li>"
        for task_id in PIPELINE_TASK_IDS
        if task_id in state_by_task_id
    ]

def _collect_failed_task_details(dag_run, context_task_instance=None) -> list[dict]:
    task_instances = _get_task_instances(dag_run, context_task_instance)
    dag_id = getattr(dag_run, "dag_id", "") or ""
    run_id = getattr(dag_run, "run_id", "") or ""
    failed_tasks = []
    for task_instance in task_instances:
        state = getattr(task_instance, "state", None)
        if state not in {"failed", "upstream_failed"}:
            continue

        task_id = getattr(task_instance, "task_id", "unknown")
        try_number = getattr(task_instance, "try_number", "unknown")
        failed_tasks.append(
            {
                "task_id": task_id,
                "state": state,
                "try_number": try_number,
                "log_url": _build_log_url(dag_id, task_id, run_id, try_number, task_instance),
            }
        )
    return failed_tasks

def _collect_relevant_failed_task_details(dag, dag_run, context_task_instance=None) -> list[dict]:
    failed_tasks = _collect_failed_task_details(dag_run, context_task_instance)
    if not failed_tasks:
        return []

    if dag is None or context_task_instance is None or not getattr(context_task_instance, "task_id", None):
        return failed_tasks

    task_map = _get_task_instance_lookup(dag_run, context_task_instance)
    lineage = _walk_error_lineage(
        dag,
        task_map,
        getattr(context_task_instance, "task_id", ""),
        metrics={},
        dag_run=dag_run,
    )
    lineage_task_ids = {item.get("task_id") for item in lineage if item.get("task_id")}
    relevant_failed_tasks = [item for item in failed_tasks if item.get("task_id") in lineage_task_ids]
    return relevant_failed_tasks or failed_tasks

def _infer_failed_task_from_lineage(dag, dag_run, context_task_instance=None, metrics: dict | None = None) -> dict | None:
    if context_task_instance is None or not getattr(context_task_instance, "task_id", None):
        return None

    triggered_task_id = getattr(context_task_instance, "task_id", None)
    metrics = metrics or {}
    if dag is not None:
        task_map = _get_task_instance_lookup(dag_run, context_task_instance)
        lineage = _walk_error_lineage(
            dag,
            task_map,
            triggered_task_id,
            metrics,
            dag_run=dag_run,
        )

        candidate = None
        for item in reversed(lineage):
            task_id = item.get("task_id")
            state = item.get("state")
            has_metrics = task_id in metrics

            if state == "failed":
                return item
            if state == "upstream_failed":
                continue
            if task_id == triggered_task_id:
                continue
            if task_id in PIPELINE_TASK_IDS:
                if not has_metrics:
                    candidate = item   # keep walking further upstream
                else:
                    break              # hit a successful task; stop here

        if candidate is not None:
            inferred = dict(candidate)
            inferred["state"] = inferred.get("state") or "inferred_failed"
            inferred["inferred"] = True
            return inferred

    if triggered_task_id in PIPELINE_TASK_IDS:
        triggered_index = PIPELINE_TASK_IDS.index(triggered_task_id)
        # Iterate FORWARD so we return the earliest task without metrics.
        # Reversing would blame the task closest to the trigger (e.g. etl_facts)
        # even when a farther-upstream task (e.g. etl_dimensions) actually failed.
        dag_id = dag.dag_id if dag is not None else ""
        run_id = getattr(dag_run, "run_id", "") or ""
        for task_id in PIPELINE_TASK_IDS[:triggered_index]:
            if task_id not in metrics:
                return {
                    "task_id": task_id,
                    "state": "inferred_failed",
                    "try_number": "unknown",
                    "log_url": _build_log_url(dag_id, task_id, run_id),
                    "inferred": True,
                }
    return None

def _resolve_root_cause_tasks(dag, dag_run, context_task_instance=None, metrics: dict | None = None) -> list[dict]:
    failed_tasks = _collect_relevant_failed_task_details(dag, dag_run, context_task_instance)
    if failed_tasks:
        return failed_tasks

    inferred_task = _infer_failed_task_from_lineage(dag, dag_run, context_task_instance, metrics)
    if inferred_task is not None:
        return [
            {
                "task_id": inferred_task.get("task_id", "unknown"),
                "state": inferred_task.get("state", "unknown"),
                "try_number": inferred_task.get("try_number", "unknown"),
                "log_url": inferred_task.get("log_url", ""),
                "inferred": True,
            }
        ]
    return []

def _get_task_instance_lookup(dag_run, context_task_instance=None) -> dict:
    task_instances = _get_task_instances(dag_run, context_task_instance)
    return {
        getattr(task_instance, "task_id", None): task_instance
        for task_instance in task_instances
        if getattr(task_instance, "task_id", None)
    }

def _task_summary(task_instance, metrics: dict | None = None, upstream_task_ids: list[str] | None = None, dag_run=None) -> dict:
    if task_instance is None:
        return {}

    task_id = getattr(task_instance, "task_id", "unknown")
    dag_id = getattr(task_instance, "dag_id", "") or ""
    run_id = getattr(dag_run, "run_id", "") if dag_run else (getattr(task_instance, "run_id", "") or "")
    try_number = getattr(task_instance, "try_number", "unknown")
    return {
        "task_id": task_id,
        "state": getattr(task_instance, "state", "unknown"),
        "try_number": try_number,
        "log_url": _build_log_url(dag_id, task_id, run_id, try_number, task_instance),
        "upstream_task_ids": upstream_task_ids or [],
        "returned_metrics": (metrics or {}).get(task_id),
    }

def _walk_error_lineage(dag, task_map: dict, task_id: str, metrics: dict, visited: set[str] | None = None, dag_run=None) -> list[dict]:
    if not dag or not task_id:
        return []

    if visited is None:
        visited = set()
    if task_id in visited:
        return []
    visited.add(task_id)

    try:
        task = dag.get_task(task_id)
    except Exception:
        return []

    lineage = []
    upstream_ids = sorted(task.upstream_task_ids)
    for upstream_id in upstream_ids:
        lineage.extend(_walk_error_lineage(dag, task_map, upstream_id, metrics, visited, dag_run))

    task_instance = task_map.get(task_id)
    if task_instance is not None:
        lineage.append(_task_summary(task_instance, metrics, upstream_ids, dag_run))
    return lineage

def _select_impacted_task_instance(task_instance, task_map: dict):
    if task_instance is not None and getattr(task_instance, "state", None) in {"failed", "upstream_failed"}:
        return task_instance

    for state in ("failed", "upstream_failed"):
        for candidate in task_map.values():
            if getattr(candidate, "state", None) == state:
                return candidate
    return None

def _build_openlineage_failure_event(context: dict, status_text: str, failure_reason: str, metrics: dict) -> dict | None:
    dag = context.get("dag")
    dag_run = context.get("dag_run")
    context_task_instance = context.get("ti") or context.get("task_instance")
    task_map = _get_task_instance_lookup(dag_run, context_task_instance)
    impacted_task_instance = _select_impacted_task_instance(
        context_task_instance,
        task_map,
    )
    if impacted_task_instance is None:
        return None

    lineage = _walk_error_lineage(
        dag,
        task_map,
        getattr(impacted_task_instance, "task_id", ""),
        metrics,
        dag_run=dag_run,
    )
    root_cause = next((item for item in lineage if item.get("state") == "failed"), None)
    if root_cause is None and lineage:
        root_cause = lineage[-1]

    silent_corruption_hint = (
        getattr(impacted_task_instance, "state", None) == "failed"
        and len(lineage) > 1
        and all(item.get("state") == "success" for item in lineage[:-1] if item)
    )

    dag_id = dag.dag_id if dag else "unknown"
    run_id = getattr(dag_run, "run_id", "manual")
    impacted_task_id = getattr(impacted_task_instance, "task_id", "unknown")
    ol_run_id = str(uuid5(NAMESPACE_URL, f"{dag_id}:{run_id}:{impacted_task_id}:{status_text}"))
    event_type = "FAIL" if "FAILED" in status_text else "OTHER"

    event_payload = {
        "eventType": event_type,
        "eventTime": pendulum.now("UTC").to_iso8601_string(),
        "producer": OPENLINEAGE_PRODUCER,
        "job": {
            "namespace": OPENLINEAGE_NAMESPACE,
            "name": f"{dag_id}.{impacted_task_id}",
        },
        "run": {
            "runId": ol_run_id,
            "facets": {
                "errorLineage": {
                    "_producer": OPENLINEAGE_PRODUCER,
                    "status": status_text,
                    "dagId": dag_id,
                    "airflowRunId": run_id,
                    "logicalDate": str(context.get("logical_date")),
                    "failureReason": failure_reason,
                    "impactedTask": _task_summary(impacted_task_instance, metrics, lineage[-1].get("upstream_task_ids", []) if lineage else [], dag_run),
                    "rootCauseTask": root_cause,
                    "lineage": lineage,
                    "notes": [
                        "Possible silent upstream data issue despite successful parent task."
                        if silent_corruption_hint
                        else "Root cause inferred from nearest failed task in the upstream chain."
                    ],
                }
            },
        },
        "inputs": [],
        "outputs": [],
    }
    return event_payload

def _emit_openlineage_event(event_payload: dict):
    try:
        from openlineage.client.client import OpenLineageClient
        from openlineage.client.facet import BaseFacet
        from openlineage.client.run import Job, Run, RunEvent, RunState
        import attr

        @attr.define
        class ErrorLineageFacet(BaseFacet):
            status: str = ""
            dagId: str = ""
            airflowRunId: str = ""
            logicalDate: str = ""
            failureReason: str = ""
            impactedTask: dict = attr.Factory(dict)
            rootCauseTask: dict = attr.Factory(dict)
            lineage: list[dict] = attr.Factory(list)
            notes: list[str] = attr.Factory(list)

        facet_payload = event_payload["run"]["facets"]["errorLineage"]
        event = RunEvent(
            eventType=RunState[event_payload["eventType"]],
            eventTime=event_payload["eventTime"],
            run=Run(
                runId=event_payload["run"]["runId"],
                facets={"errorLineage": ErrorLineageFacet(**facet_payload)},
            ),
            job=Job(
                namespace=event_payload["job"]["namespace"],
                name=event_payload["job"]["name"],
            ),
            producer=event_payload["producer"],
            inputs=[],
            outputs=[],
        )
        OpenLineageClient().emit(event)
    except Exception as exc:
        log_etl(f"[openlineage] Failed to emit lineage event: {exc}")

def _format_openlineage_failure_text(event_payload: dict) -> str:
    facet = ((event_payload.get("run") or {}).get("facets") or {}).get("errorLineage") or {}
    impacted = facet.get("impactedTask") or {}
    root_cause = facet.get("rootCauseTask") or {}
    lineage = facet.get("lineage") or []
    notes = facet.get("notes") or []

    def _has_meaningful_task_data(item: dict | None) -> bool:
        if not item:
            return False
        return any(
            value not in (None, "", "unknown", [], {})
            for value in (
                item.get("task_id"),
                item.get("state"),
                item.get("try_number"),
                item.get("log_url"),
                item.get("returned_metrics"),
                item.get("upstream_task_ids"),
            )
        )

    lineage = [item for item in lineage if _has_meaningful_task_data(item)]
    has_root_cause = _has_meaningful_task_data(root_cause)

    lines = [
        "IMS Pipeline Error Lineage",
        f"Status: {facet.get('status', 'unknown')}",
        f"DAG: {facet.get('dagId', 'unknown')}",
        f"Airflow Run ID: {facet.get('airflowRunId', 'unknown')}",
        f"Logical Date: {facet.get('logicalDate', 'unknown')}",
        f"Failure Reason: {facet.get('failureReason', 'unknown')}",
        "",
        "Impacted Task:",
        f"- Task ID: {impacted.get('task_id', 'unknown')}",
        f"- State: {impacted.get('state', 'unknown')}",
        f"- Try Number: {impacted.get('try_number', 'unknown')}",
        f"- Log URL: {impacted.get('log_url', '')}",
        "",
    ]

    if has_root_cause:
        lines.extend(
            [
                "Likely Root Cause:",
                f"- Task ID: {root_cause.get('task_id', 'unknown')}",
                f"- State: {root_cause.get('state', 'unknown')}",
                f"- Try Number: {root_cause.get('try_number', 'unknown')}",
                f"- Log URL: {root_cause.get('log_url', '')}",
                "",
            ]
        )

    lines.append("Upstream Lineage:")

    if lineage:
        for item in lineage:
            upstream = item.get("upstream_task_ids") or []
            lines.extend(
                [
                    f"- {item.get('task_id', 'unknown')}",
                    f"  state: {item.get('state', 'unknown')}",
                    f"  try_number: {item.get('try_number', 'unknown')}",
                    f"  upstream_task_ids: {', '.join(upstream) if upstream else 'none'}",
                    f"  log_url: {item.get('log_url', '')}",
                    f"  returned_metrics: {json.dumps(item.get('returned_metrics'), default=str)}",
                ]
            )
    else:
        lines.append("- No lineage details were available")

    if notes and (has_root_cause or lineage):
        lines.extend(["", "Notes:"])
        lines.extend(f"- {note}" for note in notes)

    lines.extend(
        [
            "",
            "OpenLineage Metadata:",
            f"- Event Type: {event_payload.get('eventType', 'unknown')}",
            f"- Event Time: {event_payload.get('eventTime', 'unknown')}",
            f"- Producer: {event_payload.get('producer', 'unknown')}",
            f"- Job Namespace: {((event_payload.get('job') or {}).get('namespace', 'unknown'))}",
            f"- Job Name: {((event_payload.get('job') or {}).get('name', 'unknown'))}",
            f"- OpenLineage Run ID: {((event_payload.get('run') or {}).get('runId', 'unknown'))}",
        ]
    )
    return "\n".join(lines)

def _format_basic_failure_text(
    context: dict,
    status_text: str,
    failure_reason: str,
    failed_tasks: list[dict],
    metrics: dict,
) -> str:
    dag = context.get("dag")
    dag_run = context.get("dag_run")
    task_instance = context.get("ti") or context.get("task_instance")

    lines = [
        "IMS Pipeline Failure Details",
        f"Status: {status_text}",
        f"DAG: {dag.dag_id if dag else 'unknown'}",
        f"Airflow Run ID: {getattr(dag_run, 'run_id', 'unknown')}",
        f"Logical Date: {context.get('logical_date')}",
        f"Triggered Task: {getattr(task_instance, 'task_id', 'unknown')}",
        f"Failure Reason: {failure_reason}",
        "",
        "Failed Tasks:",
    ]

    if failed_tasks:
        lines.extend(
            [
                f"Likely Root Cause Task: {failed_tasks[0].get('task_id', 'unknown')}",
                f"Likely Root Cause State: {failed_tasks[0].get('state', 'unknown')}",
                "",
            ]
        )

    if failed_tasks:
        for item in failed_tasks:
            lines.extend(
                [
                    f"- Task ID: {item.get('task_id', 'unknown')}",
                    f"  State: {item.get('state', 'unknown')}",
                    f"  Try Number: {item.get('try_number', 'unknown')}",
                    f"  Inferred: {'yes' if item.get('inferred') else 'no'}",
                    f"  Log URL: {item.get('log_url', '')}",
                ]
            )
    else:
        lines.append("- No failed tasks were recorded")

    lines.extend(["", "Returned Metrics:"])
    if metrics:
        for task_id, payload in metrics.items():
            lines.append(f"- {task_id}: {json.dumps(payload, default=str)}")
    else:
        lines.append("- No task metrics were available for this run.")

    lines.extend(
        [
            "",
            "Notes:",
            "- OpenLineage details were unavailable, so this fallback report was attached instead.",
        ]
    )
    return "\n".join(lines)

def _format_failure_reason(context: dict, dag_run, task_instance) -> str:
    dag = context.get("dag")
    exception = context.get("exception")
    if exception:
        return str(exception)

    failed_tasks = _resolve_root_cause_tasks(
        dag,
        dag_run,
        task_instance,
        _collect_run_metrics(context),
    )
    if failed_tasks:
        primary_failed = next((item for item in failed_tasks if item["state"] == "failed"), failed_tasks[0])
        related_tasks = "; ".join(
            f"{item['task_id']} ({item['state']}, try {item['try_number']})"
            for item in failed_tasks
            if item["task_id"] != primary_failed["task_id"]
        )
        if primary_failed.get("inferred"):
            message = (
                f"Inferred root cause task: {primary_failed['task_id']} "
                f"({primary_failed['state']}, try {primary_failed['try_number']}). "
                f"Airflow had not yet recorded a concrete failed task state when the DAG failure callback ran."
            )
        else:
            message = (
                f"Root cause task: {primary_failed['task_id']} "
                f"({primary_failed['state']}, try {primary_failed['try_number']})"
            )
        if related_tasks:
            message += f"; downstream/related task states: {related_tasks}"
        return message

    if task_instance is not None:
        return (
            f"{getattr(task_instance, 'task_id', 'unknown')} entered state "
            f"{getattr(task_instance, 'state', 'unknown')}. Check task logs for the exact stack trace."
        )

    return "Airflow marked the pipeline as failed, but no exception text was attached to the DAG callback."

def _infer_smtp_settings() -> tuple[str, int]:
    if ALERT_SMTP_HOST and ALERT_SMTP_PORT:
        return ALERT_SMTP_HOST, int(ALERT_SMTP_PORT)

    sender_domain = (ALERT_FROM_EMAIL or "").split("@")[-1].lower()
    if sender_domain == "gmail.com":
        return "smtp.gmail.com", 587
    if sender_domain in {"outlook.com", "hotmail.com", "live.com", "office365.com"}:
        return "smtp.office365.com", 587

    raise RuntimeError(
        "SMTP host/port not configured. Set ALERT_SMTP_HOST and ALERT_SMTP_PORT in .env."
    )

def _send_alert_email(subject: str, html_content: str, attachments: list[tuple[str, str, str]] | None = None):
    smtp_host, smtp_port = _infer_smtp_settings()
    if not ALERT_SMTP_USERNAME or not ALERT_SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP credentials missing. Set ALERT_SMTP_USERNAME and ALERT_SMTP_PASSWORD in .env."
        )

    # Use a multipart/mixed root so attachments are rendered consistently by mail clients.
    message = MIMEMultipart("mixed")
    body = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = ALERT_FROM_EMAIL or ""
    message["To"] = ALERT_TO_EMAIL or ""
    body.attach(MIMEText("IMS pipeline notification. Use an HTML-capable mail client for full details.", "plain", "utf-8"))
    body.attach(MIMEText(html_content, "html", "utf-8"))
    message.attach(body)
    for filename, content, content_type in attachments or []:
        if content_type == "text/plain":
            attachment = MIMEText(content, "plain", "utf-8")
        else:
            attachment = MIMEApplication(content.encode("utf-8"), _subtype="json")
        attachment.add_header("Content-Disposition", "attachment", filename=filename)
        message.attach(attachment)

    smtp_client_cls = smtplib.SMTP_SSL if ALERT_SMTP_SSL else smtplib.SMTP
    with smtp_client_cls(host=smtp_host, port=smtp_port, timeout=30) as smtp_client:
        if ALERT_SMTP_STARTTLS and not ALERT_SMTP_SSL:
            smtp_client.starttls()
        smtp_client.login(ALERT_SMTP_USERNAME, ALERT_SMTP_PASSWORD)
        smtp_client.sendmail(
            ALERT_FROM_EMAIL,
            [email.strip() for email in (ALERT_TO_EMAIL or "").split(",") if email.strip()],
            message.as_string(),
        )
 

def _send_pipeline_status_email(context: dict, status_text: str):
    if not ALERT_FROM_EMAIL or not ALERT_TO_EMAIL:
        log_etl(f"[email_alert] Skipped {status_text.lower()} notification because email env vars are missing")
        return

    dag = context.get("dag")
    dag_run = context.get("dag_run")
    ti = context.get("ti")
    task_instance = ti or context.get("task_instance")
    metrics = _collect_run_metrics(context)
    metrics_html = _format_metrics_html(metrics)

    task_states = _collect_task_states(dag_run, task_instance)
    details_html = ""
    attachments = []
    if status_text != "SUCCESS":
        failure_reason = _format_failure_reason(context, dag_run, task_instance)
        failed_tasks = _resolve_root_cause_tasks(dag, dag_run, task_instance, metrics)
        lineage_event = _build_openlineage_failure_event(context, status_text, failure_reason, metrics)
        attachment_name = (
            f"openlineage_error_lineage_{getattr(dag_run, 'run_id', 'manual').replace(':', '_')}.txt"
        )
        if lineage_event is not None:
            attachment_text = _format_openlineage_failure_text(lineage_event)
            _emit_openlineage_event(lineage_event)
        else:
            attachment_text = _format_basic_failure_text(
                context,
                status_text,
                failure_reason,
                failed_tasks,
                metrics,
            )
            log_etl(
                f"[email_alert] Falling back to basic failure attachment for run "
                f"{getattr(dag_run, 'run_id', 'unknown')}"
            )
        attachments.append((attachment_name, attachment_text, "text/plain"))
        failed_tasks_html = "".join(
            (
                f"<li><b>{item['task_id']}</b> - {item['state']} "
                    f"(try {item['try_number']}) "
                    f"{'(inferred) ' if item.get('inferred') else ''}"
                    f"<a href=\"{item['log_url']}\">task log</a></li>"
            )
            for item in failed_tasks
        )
        details_html = f"""
        <p><b>Reason:</b> {failure_reason}</p>
        <p><b>OpenLineage Attachment:</b> The mail includes a txt file with the inferred error lineage.</p>
        <h4>Failed Tasks</h4>
        <ul>{failed_tasks_html or '<li>No failed tasks were recorded</li>'}</ul>
        """

    html_content = f"""
    <h3>IMS Pipeline Run {status_text}</h3>
    <p><b>DAG:</b> {dag.dag_id if dag else 'unknown'}</p>
    <p><b>Run ID:</b> {getattr(dag_run, 'run_id', 'unknown')}</p>
    <p><b>Run Status:</b> {status_text}</p>
    <p><b>Logical Date:</b> {context.get('logical_date')}</p>
    <p><b>Triggered Task:</b> {getattr(task_instance, 'task_id', 'N/A')}</p>
    {details_html}
    <h4>Task States</h4>
    <ul>{''.join(task_states) or '<li>No task states available</li>'}</ul>
    <h4>Returned Metrics</h4>
    {metrics_html}
    """

    _send_alert_email(
        subject=f"[Airflow] IMS Pipeline {status_text} - {getattr(dag_run, 'run_id', 'manual')}",
        html_content=html_content,
        attachments=attachments,
    )
    if attachments:
        log_etl(
            f"[email_alert] Attached files for run {getattr(dag_run, 'run_id', 'unknown')}: "
            + ", ".join(filename for filename, _, _ in attachments)
        )
    log_etl(f"[email_alert] Sent {status_text.lower()} notification for run {getattr(dag_run, 'run_id', 'unknown')}")

def notify_pipeline_success(context: dict):
    try:
        _send_pipeline_status_email(context, "SUCCESS")
    except Exception as exc:
        log_etl(f"[email_alert] Failed success notification: {exc}")

def notify_pipeline_failure(context: dict):
    try:
        _send_pipeline_status_email(context, "FAILED")
    except Exception as exc:
        log_etl(f"[email_alert] Failed failure notification: {exc}")

def notify_task_failure(context: dict):
    try:
        _send_pipeline_status_email(context, "TASK FAILED")
    except Exception as exc:
        log_etl(f"[email_alert] Failed task failure notification: {exc}")

def notify_task_retry(context: dict):
    try:
        task_instance = context.get("ti") or context.get("task_instance")
        next_retry = ""
        retry_getter = getattr(task_instance, "next_retry_datetime", None)
        if callable(retry_getter):
            try:
                next_retry = retry_getter()
            except Exception:
                next_retry = ""

        context = {
            **context,
            "exception": context.get("exception")
            or f"Task is up for retry. Next retry at: {next_retry or 'calculated by Airflow scheduler'}",
        }
        _send_pipeline_status_email(context, "TASK UP FOR RETRY")
    except Exception as exc:
        log_etl(f"[email_alert] Failed retry notification: {exc}")

default_args.update(
    {
        "on_failure_callback": notify_task_failure,
        "on_retry_callback": notify_task_retry,
    }
)

dag = DAG(
    dag_id="ims_daily_pipeline_v2",
    default_args=default_args,
    description="IMS: MySQL OLTP → PostgreSQL OLAP + daily analytics",
    schedule="@daily",
    start_date=pendulum.datetime(2026, 3, 6, tz="Asia/Kolkata"),
    catchup=False,
    max_active_runs=1,
    tags=["ims", "etl", "attendance"],
    on_success_callback=notify_pipeline_success,
    on_failure_callback=notify_pipeline_failure,
)


def _safe_close(*sessions):
    """Close database sessions safely"""
    for s in sessions:
        try:
            s.close()
        except Exception:
            pass

def stage_golden_source(**kwargs):
    """Extract new or changed OLTP rows into transient MySQL golden tables."""
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from crud.golden_source_ops import extract_incremental_to_golden

    mysql_db = MYSQL_SessionLocal()
    try:
        result = extract_incremental_to_golden(mysql_db)
        log_etl(f"[stage_golden_source] Extracted incremental golden rows: {result['counts']}")
        return result
    except Exception as e:
        log_etl(f"[stage_golden_source] Error: {e}")
        raise
    finally:
        _safe_close(mysql_db)


def create_golden_snapshot(**kwargs):
    """Persist the transient MySQL golden copy as a snapshot batch."""
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from crud.golden_source_ops import create_snapshot_batch

    mysql_db = None
    try:
        mysql_db = MYSQL_SessionLocal()
        result = create_snapshot_batch(mysql_db)
        log_etl(f"[create_golden_snapshot] Created batch {result['batch_id']} with counts {result['counts']}")
        return result
    except Exception as e:
        log_etl(f"[create_golden_snapshot] Error: {e}")
        raise
    finally:
        _safe_close(mysql_db)

def etl_dimensions(**kwargs):
    """Load PostgreSQL dimensions from one MySQL snapshot batch."""
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from crud.golden_source_ops import load_dimensions_from_snapshot

    ti = kwargs["ti"]
    batch_info = ti.xcom_pull(task_ids="create_golden_snapshot")
    batch_id = batch_info["batch_id"]

    mysql_db = None
    pg_db = None
    try:
        mysql_db = MYSQL_SessionLocal()
        synced = load_dimensions_from_snapshot(mysql_db, pg_db, batch_id)
        log_etl(f"[etl_dimensions] Batch {batch_id}: {synced}")
        return {"batch_id": batch_id, "synced": synced}
    except Exception as e:
        log_etl(f"[etl_dimensions] Error: {e}")
        raise
    finally:
        _safe_close(mysql_db, pg_db)

def etl_facts(**kwargs):
    """Load PostgreSQL facts from one MySQL snapshot batch."""
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from crud.golden_source_ops import load_facts_from_snapshot

    ti = kwargs["ti"]
    batch_info = ti.xcom_pull(task_ids="create_golden_snapshot")
    batch_id = batch_info["batch_id"]

    mysql_db = None
    pg_db = None
    try:
        mysql_db = MYSQL_SessionLocal()
        pg_db = PG_SessionLocal()
        synced = load_facts_from_snapshot(mysql_db, pg_db, batch_id)
        log_etl(f"[etl_facts] Batch {batch_id}: {synced}")
        return {"batch_id": batch_id, "synced": synced}
    except Exception as e:
        log_etl(f"[etl_facts] Error: {e}")
        raise
    finally:
        _safe_close(mysql_db, pg_db)

def finalize_golden_batch(**kwargs):
    """Advance watermarks and clear transient MySQL golden tables after success."""
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from crud.golden_source_ops import finalize_batch

    ti = kwargs["ti"]
    extraction_result = ti.xcom_pull(task_ids="stage_golden_source")
    batch_info = ti.xcom_pull(task_ids="create_golden_snapshot")
    batch_id = batch_info["batch_id"]

    mysql_db = None
    try:
        mysql_db = MYSQL_SessionLocal()
        result = finalize_batch(mysql_db, batch_id, extraction_result)
        log_etl(f"[finalize_golden_batch] Finalized batch {result['batch_id']} with status {result['status']}")
        return result
    except Exception as e:
        log_etl(f"[finalize_golden_batch] Error: {e}")
        raise
    finally:
        _safe_close(mysql_db)

def generate_faker_data(**kwargs):
    """Generate daily fake attendance data"""
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from crud.faker_data_generator import generate_student_attendance, generate_faculty_attendance
    from schemas.student import MYSQL_Students
    from schemas.faculty import MYSQL_Faculty
    
    mysql_db = MYSQL_SessionLocal()
    try:
        students = mysql_db.query(MYSQL_Students).all()
        faculty = mysql_db.query(MYSQL_Faculty).all()
        stu_res = generate_student_attendance(mysql_db, students, days_back=1)
        fac_res = generate_faculty_attendance(mysql_db, faculty, days_back=1)
        log_etl(f"[generate_faker_data] Student attendance: {stu_res}, Faculty attendance: {fac_res}")
        return {
            "student_attendance": stu_res,
            "faculty_attendance": fac_res,
        }
    except Exception as e:
        log_etl(f"[generate_faker_data] Error: {e}")
        raise
    finally:
        _safe_close(mysql_db)

def generate_salary(**kwargs):
    """Generate monthly salary records (runs on 1st of month only)"""
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from crud.salary_ops import generate_monthly_salary
    
    today = date.today()
    if today.day != 1:
        log_etl("[salary] Not 1st of month — skipping")
        return {"status": "skipped", "reason": "not_first_day_of_month"}
    
    mysql_db = MYSQL_SessionLocal()
    try:
        records = generate_monthly_salary(mysql_db, today.month, today.year)
        log_etl(f"[salary] Generated {len(records)} salary records for {today.month}/{today.year}")
        return {
            "status": "generated",
            "records": len(records),
            "month": today.month,
            "year": today.year,
        }
    except Exception as e:
        log_etl(f"[salary] Error: {e}")
        raise
    finally:
        _safe_close(mysql_db)

def calc_teacher_performance(**kwargs):
    """Calculate teacher performance metrics"""
    from dotenv import load_dotenv
    load_dotenv(IMS_ENV_PATH)
    from schemas.faculty import PG_Faculty
    from schemas.faculty_attendance import PGFacultyAttendance
    from schemas.scores import PGStudentScores
    from uuid import uuid4
    from sqlalchemy import text
    import datetime as dt
    
    today = dt.date.today()
    pg_db = PG_SessionLocal()
    inserted = 0
    try:
        faculty_list = pg_db.query(PG_Faculty).all()
        for f in faculty_list:
            att_records = pg_db.query(PGFacultyAttendance).filter(
                PGFacultyAttendance.faculty_id == f.id).all()
            total = len(att_records)
            present = sum(1 for a in att_records if a.is_present)
            att_pct = round((present / total * 100), 2) if total > 0 else 0.0

            scores = pg_db.query(PGStudentScores).filter(
                PGStudentScores.lecturer_id == f.id).all()
            avg_score = round(sum(s.avg_marks for s in scores if s.avg_marks) / len(scores), 2) if scores else None

            perf_score = round(0.4 * att_pct + (0.6 * avg_score if avg_score else 0), 2)

            pg_db.execute(
                text(
                    "INSERT INTO dim_teacher_performance "
                    "(id,faculty_id,faculty_name,total_classes,attended_classes,"
                    "attendance_pct,avg_student_score,performance_score,month,year) "
                    "VALUES (:id,:fid,:fname,:total,:present,:att_pct,:avg,:perf,:month,:year) "
                    "ON CONFLICT DO NOTHING"
                ),
                {"id": str(uuid4()), "fid": str(f.id), "fname": f.name,
                 "total": total, "present": present, "att_pct": att_pct,
                 "avg": avg_score, "perf": perf_score,
                 "month": today.month, "year": today.year}
            )
            inserted += 1
        pg_db.commit()
        log_etl(f"[teacher_perf] Calculated for {len(faculty_list)} faculty")
        return {
            "faculty_processed": len(faculty_list),
            "rows_attempted": inserted,
            "month": today.month,
            "year": today.year,
        }
    except Exception as e:
        log_etl(f"[teacher_perf] Error: {e}")
        raise
    finally:
        _safe_close(pg_db)

# ========== DEFINE TASKS ==========

start = EmptyOperator(task_id="start", dag=dag)
end = EmptyOperator(task_id="end", dag=dag)

t_stage_golden = PythonOperator(task_id="stage_golden_source", python_callable=stage_golden_source, dag=dag)
t_snapshot = PythonOperator(task_id="create_golden_snapshot", python_callable=create_golden_snapshot, dag=dag)
t_dimensions = PythonOperator(task_id="etl_dimensions", python_callable=etl_dimensions, dag=dag)
t_facts = PythonOperator(task_id="etl_facts", python_callable=etl_facts, dag=dag)
t_gen_data = PythonOperator(task_id="gen_daily_attendance", python_callable=generate_faker_data, dag=dag)
t_salary = PythonOperator(task_id="generate_salary", python_callable=generate_salary, dag=dag)
t_performance = PythonOperator(task_id="teacher_performance", python_callable=calc_teacher_performance, dag=dag)
t_finalize = PythonOperator(task_id="finalize_golden_batch", python_callable=finalize_golden_batch, dag=dag)

# ========== TASK DEPENDENCIES ==========

# Generate fresh operational-side data first, then snapshot it into golden staging.
start >> [t_gen_data, t_salary]
[t_gen_data, t_salary] >> t_stage_golden

t_stage_golden >> t_snapshot
t_snapshot >> t_dimensions
t_dimensions >> t_facts
t_facts >> t_performance
t_performance >> t_finalize
t_finalize >> end
