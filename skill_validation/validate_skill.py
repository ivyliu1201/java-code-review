#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REQUIRED_SOURCES = [
    "SKILL.md",
    "references/report-templates.md",
    "references/review-workflow.md",
    "references/java-rules.md",
]

MANAGED_OUTPUT_FILES = {
    "validation_results.jsonl",
    "requirements_coverage.json",
    "validation_summary.json",
    "spec_source_manifest.json",
    "requirements_catalog.json",
}

CATEGORY_TO_TYPE = {
    "triggers": "trigger",
    "must_rules": "must",
    "must_not_rules": "must_not",
    "tool_dependencies": "tool_dependency",
    "file_dependencies": "file_dependency",
    "output_requirements": "output",
    "workflow_requirements": "workflow",
    "java_review_rules": "java_rule",
    "error_handling_requirements": "error_handling",
}

KEYWORD_HINTS = (
    "trigger",
    "must",
    "must not",
    "should",
    "必須",
    "不得",
    "不可",
    "禁止",
    "不要",
    "應",
    "需",
    "工具",
    "檔案",
    "輸出",
    "workflow",
    "java rule",
    "error",
    "例外",
    "錯誤",
    "風險",
    ".md",
    "java",
    "review",
    "report",
    "template",
    "scope",
    "ledger",
    "batch",
    "inventory",
)

TRIGGER_TERMS = (
    "java",
    "code review",
    "production java",
    "spring",
    "spring boot",
    "重構",
    "命名",
    "常數",
    "布林",
    "審查",
    "規範",
)

NEGATIVE_SCOPE_TERMS = (
    "python",
    "vue",
    "react",
    "frontend",
    "css",
    "html",
    "會議紀錄",
    "簡報",
)

MUST_NOT_TERMS = ("不得", "不可", "禁止", "不要", "must not", "do not")
MUST_TERMS = ("必須", "一律", "應", "需", "should", "must")
OUTPUT_TERMS = (
    "輸出",
    "模板",
    "report",
    "summary",
    "review scope",
    "findings",
    "open questions",
    "residual risks",
    "review ledger",
    "progress",
    "continuation prompt",
)
WORKFLOW_TERMS = (
    "流程",
    "步驟",
    "inventory",
    "batch",
    "ledger",
    "mode",
    "scope",
    "reviewed files",
    "continue",
    "續審",
    "完成條件",
)
TOOL_TERMS = ("tool", "工具", "codex", "cli", "runtime", "python 3", "標準函式庫")
ERROR_TERMS = ("無法", "失敗", "錯誤", "例外", "缺少", "缺失", "風險", "不可宣稱")

RUNTIME_ENV_KEY = "CODEX_RUNTIME_COMMAND"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a Codex skill specification.")
    parser.add_argument("--skill-root", default=".", help="Skill root directory.")
    parser.add_argument("--output-dir", required=True, help="Validation output directory.")
    parser.add_argument(
        "--validation-mode",
        choices=("auto", "runtime", "static"),
        default="auto",
        help="Validation mode selection.",
    )
    return parser.parse_args()


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def resolve_skill_root(requested_root: Path) -> Path:
    requested_root = requested_root.resolve()
    if (requested_root / "SKILL.md").exists():
        return requested_root

    fallback_root = Path(r"D:\Users\00550389\.codex\skills\java-code-review")
    if (fallback_root / "SKILL.md").exists():
        return fallback_root.resolve()

    return requested_root


def relative_to_root(path: Path, root: Path) -> str:
    return os.path.relpath(path, root)


def build_source_manifest(skill_root: Path) -> tuple[list[dict[str, Any]], dict[str, str], list[str]]:
    manifest: list[dict[str, Any]] = []
    source_texts: dict[str, str] = {}
    notes: list[str] = []

    for relative_path in REQUIRED_SOURCES:
        path = skill_root / relative_path
        item: dict[str, Any] = {
            "source_file": relative_path,
            "exists": path.exists(),
            "read_status": "missing",
            "line_count": 0,
            "char_count": 0,
            "error": None,
        }
        if path.exists():
            try:
                text = read_utf8(path)
                source_texts[relative_path] = text
                item["read_status"] = "read"
                item["line_count"] = len(text.splitlines())
                item["char_count"] = len(text)
            except Exception as exc:  # pragma: no cover - defensive path
                item["read_status"] = "error"
                item["error"] = str(exc)
                notes.append(f"{relative_path} 讀取失敗：{exc}")
        else:
            notes.append(f"{relative_path} 缺失。")
        manifest.append(item)
    return manifest, source_texts, notes


def source_alias(relative_path: str) -> str:
    mapping = {
        "SKILL.md": "skill",
        "references/report-templates.md": "report",
        "references/review-workflow.md": "workflow",
        "references/java-rules.md": "java",
    }
    return mapping.get(relative_path, "spec")


def extract_candidates(relative_path: str, text: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    lines = text.splitlines()
    heading_stack: list[tuple[int, str]] = []
    in_code_block = False
    frontmatter = False

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        if line_number == 1 and stripped == "---":
            frontmatter = True
            continue
        if frontmatter:
            if stripped == "---":
                frontmatter = False
                continue
            if stripped.startswith("description:"):
                candidates.append(
                    {
                        "line_number": line_number,
                        "heading_path": "frontmatter",
                        "text": normalize_text(stripped.partition(":")[2]),
                    }
                )
            continue

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading_match:
            level = len(heading_match.group(1))
            title = normalize_text(heading_match.group(2))
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, title))
            continue

        if not stripped:
            continue

        heading_path = " > ".join(title for _, title in heading_stack)

        list_match = re.match(r"^([-*]|\d+\.)\s+(.*)$", stripped)
        if list_match:
            candidate_text = normalize_text(list_match.group(2))
            candidates.append(
                {
                    "line_number": line_number,
                    "heading_path": heading_path,
                    "text": candidate_text,
                }
            )
            continue

        lowered = stripped.lower()
        if any(keyword in lowered for keyword in KEYWORD_HINTS):
            candidates.append(
                {
                    "line_number": line_number,
                    "heading_path": heading_path,
                    "text": normalize_text(stripped),
                }
            )

    return candidates


def classify_requirement_type(source_file: str, heading_path: str, text: str) -> str | None:
    lowered = text.lower()
    heading_lower = heading_path.lower()

    if source_file == "references/java-rules.md":
        return "java_rule"

    trigger_context = source_file == "SKILL.md" and (
        "適用範圍" in heading_path
        or "frontmatter" in heading_lower
        or "java code review" in lowered
        or "production java" in lowered
        or "重構" in text
    )
    if trigger_context:
        return "trigger"

    if ".md" in lowered or "reference" in heading_lower or "載入" in heading_path:
        return "file_dependency"

    if any(term in lowered for term in TOOL_TERMS):
        return "tool_dependency"

    if any(term in lowered for term in OUTPUT_TERMS) or "回應契約" in heading_path:
        return "output"

    if any(term in lowered for term in WORKFLOW_TERMS) or "審查模式" in heading_path or "審查原則" in heading_path:
        return "workflow"

    if any(term in lowered for term in ERROR_TERMS):
        return "error_handling"

    if any(term in lowered for term in MUST_NOT_TERMS):
        return "must_not"

    if any(term in lowered for term in MUST_TERMS):
        return "must"

    return None


def parse_requirements(source_texts: dict[str, str]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], list[str]]:
    requirements: list[dict[str, Any]] = []
    notes: list[str] = []
    categories: dict[str, list[dict[str, Any]]] = {name: [] for name in CATEGORY_TO_TYPE}

    for relative_path in REQUIRED_SOURCES:
        text = source_texts.get(relative_path)
        if text is None:
            continue
        alias = source_alias(relative_path)
        counter = 0
        for candidate in extract_candidates(relative_path, text):
            requirement_type = classify_requirement_type(
                relative_path, candidate["heading_path"], candidate["text"]
            )
            if requirement_type is None:
                continue
            counter += 1
            requirement = {
                "requirement_id": f"{alias}-r{counter:04d}",
                "source_file": relative_path,
                "requirement_type": requirement_type,
                "text": candidate["text"],
                "line_number": candidate["line_number"],
                "heading_path": candidate["heading_path"],
            }
            requirements.append(requirement)
            for category_name, mapped_type in CATEGORY_TO_TYPE.items():
                if mapped_type == requirement_type:
                    categories[category_name].append(requirement)

    for category_name, items in categories.items():
        if not items:
            notes.append(f"{category_name} 未明確定義，已輸出空陣列。")

    if not requirements:
        notes.append("未解析出任何 requirement。")

    return requirements, categories, notes


def find_requirement(
    requirements: list[dict[str, Any]],
    *,
    source_file: str | None = None,
    requirement_type: str | None = None,
    keywords: list[str] | None = None,
) -> dict[str, Any] | None:
    for requirement in requirements:
        if source_file and requirement["source_file"] != source_file:
            continue
        if requirement_type and requirement["requirement_type"] != requirement_type:
            continue
        if keywords:
            text = requirement["text"].lower()
            if not all(keyword.lower() in text for keyword in keywords):
                continue
        return requirement
    return None


def must_pick(
    requirements: list[dict[str, Any]],
    notes: list[str],
    description: str,
    **criteria: Any,
) -> dict[str, Any] | None:
    requirement = find_requirement(requirements, **criteria)
    if requirement is None:
        notes.append(f"找不到 {description} 對應 requirement。")
    return requirement


def requirement_refs(items: list[dict[str, Any] | None]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item is None:
            continue
        requirement_id = item["requirement_id"]
        if requirement_id not in seen:
            ordered.append(requirement_id)
            seen.add(requirement_id)
    return ordered


def source_refs(items: list[dict[str, Any] | None]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item is None:
            continue
        source_file = item["source_file"]
        if source_file not in seen:
            ordered.append(source_file)
            seen.add(source_file)
    return ordered


def build_cases(requirements: list[dict[str, Any]], source_manifest: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    notes: list[str] = []
    source_lookup = {item["source_file"]: item for item in source_manifest}

    trigger_review = must_pick(
        requirements,
        notes,
        "Java review 觸發條件",
        source_file="SKILL.md",
        requirement_type="trigger",
        keywords=["code review"],
    ) or must_pick(
        requirements,
        notes,
        "Java 規範觸發條件",
        source_file="SKILL.md",
        requirement_type="trigger",
        keywords=["java", "規範"],
    )
    trigger_scope = must_pick(
        requirements,
        notes,
        "適用範圍 requirement",
        source_file="SKILL.md",
        requirement_type="trigger",
        keywords=["production java"],
    ) or must_pick(
        requirements,
        notes,
        "適用範圍 fallback requirement",
        source_file="SKILL.md",
        requirement_type="trigger",
        keywords=["production"],
    )
    utf8_rule = must_pick(
        requirements,
        notes,
        "UTF-8 requirement",
        source_file="SKILL.md",
        requirement_type="must_not",
        keywords=["utf-8"],
    )
    java_rules_file = must_pick(
        requirements,
        notes,
        "java-rules file dependency",
        source_file="SKILL.md",
        requirement_type="file_dependency",
        keywords=["唯一正式來源"],
    )
    must_not_claim_local_rules = must_pick(
        requirements,
        notes,
        "無法讀取 java-rules 時不得宣稱已套用本地規則",
        source_file="SKILL.md",
        requirement_type="file_dependency",
        keywords=["不得宣稱已套用本地規則"],
    )
    must_apply_local_rules = must_pick(
        requirements,
        notes,
        "產碼必須主動套用本地規則",
        source_file="SKILL.md",
        requirement_type="must",
        keywords=["主動套用本地規則"],
    )
    must_not_invalid_code = must_pick(
        requirements,
        notes,
        "產碼不得引入明顯違規寫法",
        source_file="SKILL.md",
        requirement_type="must_not",
        keywords=["不得引入明顯違反"],
    )
    findings_first = must_pick(
        requirements,
        notes,
        "先列 findings requirement",
        source_file="SKILL.md",
        requirement_type="output",
        keywords=["先列 findings"],
    )
    severity_output = must_pick(
        requirements,
        notes,
        "嚴重度分類 requirement",
        source_file="SKILL.md",
        requirement_type="output",
        keywords=["critical"],
    )
    report_template_large = must_pick(
        requirements,
        notes,
        "Large Codebase report template",
        source_file="references/report-templates.md",
        requirement_type="output",
        keywords=["large codebase review mode"],
    )
    workflow_inventory = must_pick(
        requirements,
        notes,
        "Large Codebase inventory requirement",
        source_file="references/review-workflow.md",
        requirement_type="workflow",
        keywords=["inventory"],
    )
    workflow_pending = must_pick(
        requirements,
        notes,
        "pending 不可輸出 final summary requirement",
        source_file="references/review-workflow.md",
        requirement_type="output",
        keywords=["不可輸出 final summary"],
    )
    compact_scope = must_pick(
        requirements,
        notes,
        "Compact review scope requirement",
        source_file="references/review-workflow.md",
        requirement_type="workflow",
        keywords=["小於等於 5 個 java 檔"],
    )
    java_rule_naming = must_pick(
        requirements,
        notes,
        "Java naming rule",
        source_file="references/java-rules.md",
        requirement_type="java_rule",
        keywords=["命名"],
    )
    java_rule_priority = must_pick(
        requirements,
        notes,
        "Java review priority rule",
        source_file="references/java-rules.md",
        requirement_type="java_rule",
        keywords=["production risk"],
    ) or must_pick(
        requirements,
        notes,
        "Java review priority fallback",
        source_file="references/java-rules.md",
        requirement_type="java_rule",
        keywords=["忽略高風險"],
    )
    file_missing_case_supported = source_lookup.get("references/java-rules.md", {}).get("exists", False)

    case_specs = [
        {
            "case_id": "positive-01",
            "category": "positive",
            "prompt": "請依照本地 Java 規範 review 這個 OrderService diff，重點看交易一致性、命名與 production 風險。",
            "expected_behavior": "應觸發 skill，先以 UTF-8 讀取 java-rules，再依 findings 優先順序進行 Java review。",
            "requirements_under_test": requirement_refs([trigger_review, java_rules_file, java_rule_priority]),
            "source_files_under_test": source_refs([trigger_review, java_rules_file, java_rule_priority]),
        },
        {
            "case_id": "positive-02",
            "category": "positive",
            "prompt": "幫我檢查這段 Java 類別的命名、常數和 boolean 欄位是否違反本地規則。",
            "expected_behavior": "應觸發 skill，並以 java-rules 的命名與欄位規則作為正式依據。",
            "requirements_under_test": requirement_refs([trigger_review, java_rules_file, java_rule_naming]),
            "source_files_under_test": source_refs([trigger_review, java_rules_file, java_rule_naming]),
        },
        {
            "case_id": "positive-03",
            "category": "positive",
            "prompt": "請產生 production Java 的 Spring Boot service，並遵守本地 Java 規範。",
            "expected_behavior": "應觸發 skill，產碼時必須主動套用本地規則，且不得引入明顯違規寫法。",
            "requirements_under_test": requirement_refs([trigger_scope, java_rules_file, must_apply_local_rules, must_not_invalid_code]),
            "source_files_under_test": source_refs([trigger_scope, java_rules_file, must_apply_local_rules, must_not_invalid_code]),
        },
        {
            "case_id": "negative-01",
            "category": "negative",
            "prompt": "請 review 這段 Python 程式碼的 pandas 寫法。",
            "expected_behavior": "不應觸發 skill，因為需求不是 Java review、Java 重構或 production Java 產碼。",
            "requirements_under_test": requirement_refs([trigger_review, trigger_scope]),
            "source_files_under_test": source_refs([trigger_review, trigger_scope]),
        },
        {
            "case_id": "negative-02",
            "category": "negative",
            "prompt": "幫我調整 Vue 首頁的配色和按鈕互動。",
            "expected_behavior": "不應觸發 skill，因為需求屬於前端 UI，不在 skill 適用範圍。",
            "requirements_under_test": requirement_refs([trigger_scope]),
            "source_files_under_test": source_refs([trigger_scope]),
        },
        {
            "case_id": "negative-03",
            "category": "negative",
            "prompt": "請整理這份會議紀錄，輸出三點摘要。",
            "expected_behavior": "不應觸發 skill，因為需求沒有 Java review、產碼或重構意圖。",
            "requirements_under_test": requirement_refs([trigger_scope]),
            "source_files_under_test": source_refs([trigger_scope]),
        },
        {
            "case_id": "edge-01",
            "category": "edge",
            "prompt": "請依照本地 Java 規範 review 這個 diff，但 references/java-rules.md 目前讀不到。",
            "expected_behavior": "應標示無法套用本地規則，不得宣稱已套用本地規則；必要時可繼續，但必須揭露限制。",
            "requirements_under_test": requirement_refs([java_rules_file, must_not_claim_local_rules, utf8_rule]),
            "source_files_under_test": source_refs([java_rules_file, must_not_claim_local_rules, utf8_rule]),
        },
        {
            "case_id": "edge-02",
            "category": "edge",
            "prompt": "幫我 review 這個 PR。",
            "expected_behavior": "資訊不足時應先要求或確認 Java diff、檔案範圍與必要上下文，不能把推測當成確定 finding。",
            "requirements_under_test": requirement_refs([compact_scope, workflow_inventory]),
            "source_files_under_test": source_refs([compact_scope, workflow_inventory]),
        },
        {
            "case_id": "compliance-01",
            "category": "compliance",
            "prompt": "請正式 review 兩個 Java 檔案，輸出 findings、Open questions 和 Residual risks。",
            "expected_behavior": "應採用 Compact 模式，先列 findings，再依嚴重度分類，並能套用正式模板欄位。",
            "requirements_under_test": requirement_refs([findings_first, severity_output, compact_scope]),
            "source_files_under_test": source_refs([findings_first, severity_output, compact_scope]),
        },
        {
            "case_id": "compliance-02",
            "category": "compliance",
            "prompt": "請 review 整個 Java 專案資料夾，共 30 個檔案，並給我可續跑的正式大範圍報告。",
            "expected_behavior": "應啟用 Large Codebase Review Mode，先做 inventory，維護 ledger，未完成時不得輸出 final summary，並附 continuation prompt。",
            "requirements_under_test": requirement_refs([workflow_inventory, workflow_pending, report_template_large, java_rule_priority]),
            "source_files_under_test": source_refs([workflow_inventory, workflow_pending, report_template_large, java_rule_priority]),
        },
    ]

    if not file_missing_case_supported:
        notes.append("references/java-rules.md 缺失，edge-01 將作為缺檔驗證案例。")

    return case_specs, notes


def classify_prompt(prompt: str) -> str:
    lowered = prompt.lower()
    has_java_signal = any(term in lowered for term in TRIGGER_TERMS)
    has_negative_signal = any(term in lowered for term in NEGATIVE_SCOPE_TERMS)
    has_review_signal = "review" in lowered or "審查" in prompt or "review" in prompt.lower()

    if has_java_signal:
        return "trigger"
    if has_negative_signal and not has_java_signal:
        return "non_trigger"
    if has_review_signal:
        return "insufficient"
    return "non_trigger"


def detect_runtime_command() -> tuple[list[str] | None, str | None]:
    configured = os.environ.get(RUNTIME_ENV_KEY)
    if configured:
        return shlex.split(configured, posix=False), None

    codex_candidate = shutil.which("codex") or shutil.which("codex.cmd") or shutil.which("codex.exe")
    if codex_candidate:
        return None, (
            "偵測到 codex CLI，但未提供可審計的非互動執行命令。"
            f" 若要啟用 runtime validation，請設定環境變數 {RUNTIME_ENV_KEY}。"
        )

    return None, "找不到可審計的 Codex CLI 或等效 runtime。"


def build_runtime_command(template: list[str], prompt: str, skill_root: Path) -> list[str]:
    command: list[str] = []
    prompt_file = skill_root / "skill_validation" / "runtime_prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    replacements = {
        "{prompt}": prompt,
        "{prompt_file}": str(prompt_file),
        "{skill_root}": str(skill_root),
    }
    for part in template:
        updated = part
        for placeholder, value in replacements.items():
            updated = updated.replace(placeholder, value)
        command.append(updated)
    return command


def evaluate_static_case(case: dict[str, Any], requirements_by_id: dict[str, dict[str, Any]]) -> tuple[bool, str, str]:
    missing_requirements = [
        requirement_id
        for requirement_id in case["requirements_under_test"]
        if requirement_id not in requirements_by_id
    ]
    if missing_requirements:
        return (
            False,
            "靜態檢查失敗：case 指向不存在的 requirement。",
            f"缺少 requirement: {', '.join(missing_requirements)}",
        )

    classification = classify_prompt(case["prompt"])
    category = case["category"]

    if category == "positive":
        passed = classification == "trigger"
        actual = f"靜態判讀：prompt 分類為 {classification}。"
        reason = "positive case 應可觸發 skill。"
        return passed, actual, reason

    if category == "negative":
        passed = classification == "non_trigger"
        actual = f"靜態判讀：prompt 分類為 {classification}。"
        reason = "negative case 不應觸發 skill。"
        return passed, actual, reason

    if category == "edge":
        if case["case_id"] == "edge-01":
            passed = any("不得宣稱" in requirements_by_id[req_id]["text"] for req_id in case["requirements_under_test"])
            actual = "靜態判讀：規格包含讀不到 java-rules 時的限制揭露要求。"
            reason = "edge case 驗證缺檔時的誠實性。"
            return passed, actual, reason
        passed = classification == "insufficient"
        actual = f"靜態判讀：prompt 分類為 {classification}。"
        reason = "edge case 應揭露資訊不足，而不是直接產生確定 finding。"
        return passed, actual, reason

    if category == "compliance":
        required_sources = set(case["source_files_under_test"])
        passed = bool(case["requirements_under_test"]) and bool(required_sources)
        if case["case_id"] == "compliance-02":
            required_sources.update({"references/report-templates.md", "references/review-workflow.md"})
            passed = required_sources.issubset(set(case["source_files_under_test"]))
        actual = "靜態判讀：case 已明確綁定對應 requirement 與 source files。"
        reason = "compliance case 檢查模板、流程與規範映射是否存在。"
        return passed, actual, reason

    return False, "未知 case 類型。", "不支援的 case category。"


def evaluate_runtime_case(
    case: dict[str, Any], template: list[str], skill_root: Path
) -> tuple[bool, str, str, str | None, str | None, int | None, str | None, str | None]:
    command_list = build_runtime_command(template, case["prompt"], skill_root)
    completed = subprocess.run(
        command_list,
        cwd=skill_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )
    command_text = subprocess.list2cmdline(command_list)
    actual_behavior = "已執行 runtime prompt，需人工檢查 stdout 是否符合 skill 規格。"
    reason = "runtime validation 只記錄執行結果，不把 CLI 成功退出視為規格完全正確。"
    passed = completed.returncode == 0
    return (
        passed,
        actual_behavior,
        reason,
        command_text,
        str(skill_root),
        completed.returncode,
        completed.stdout,
        completed.stderr,
    )


def build_coverage(
    requirements: list[dict[str, Any]], results: list[dict[str, Any]]
) -> dict[str, Any]:
    covered_by_cases: dict[str, list[str]] = defaultdict(list)
    for result in results:
        if not result["passed"]:
            continue
        for requirement_id in result["requirements_under_test"]:
            covered_by_cases[requirement_id].append(result["case_id"])

    covered = []
    uncovered = []
    for requirement in requirements:
        requirement_id = requirement["requirement_id"]
        if requirement_id in covered_by_cases:
            covered.append(
                {
                    "requirement_id": requirement_id,
                    "source_file": requirement["source_file"],
                    "requirement_type": requirement["requirement_type"],
                    "text": requirement["text"],
                    "covered_by_cases": covered_by_cases[requirement_id],
                }
            )
        else:
            uncovered.append(
                {
                    "requirement_id": requirement_id,
                    "source_file": requirement["source_file"],
                    "requirement_type": requirement["requirement_type"],
                    "text": requirement["text"],
                    "reason": "沒有任何通過的 case 將此 requirement 列入 requirements_under_test。",
                }
            )

    total_requirements = len(requirements)
    covered_requirements = len(covered)
    coverage_ratio = covered_requirements / total_requirements if total_requirements else 0.0

    return {
        "covered_requirements": covered_requirements,
        "total_requirements": total_requirements,
        "coverage_ratio": round(coverage_ratio, 4),
        "covered": covered,
        "uncovered": uncovered,
        "notes": [],
    }


def gate_a_status(source_manifest: list[dict[str, Any]]) -> tuple[str, list[str]]:
    notes: list[str] = []
    skill_item = next((item for item in source_manifest if item["source_file"] == "SKILL.md"), None)
    if not skill_item or not skill_item["exists"]:
        notes.append("SKILL.md 缺失。")
    references = [item for item in source_manifest if item["source_file"] != "SKILL.md"]
    if references and all(not item["exists"] for item in references):
        notes.append("所有 reference files 都缺失。")
    for item in source_manifest:
        if item["exists"] and item["read_status"] != "read":
            notes.append(f"{item['source_file']} 讀取狀態為 {item['read_status']}。")
    return ("fail" if notes else "pass"), notes


def gate_b_status(requirements: list[dict[str, Any]], parser_notes: list[str]) -> tuple[str, list[str]]:
    notes: list[str] = []
    if not requirements:
        notes.append("無法解析任何 requirement。")
    required_keys = {"requirement_id", "source_file", "requirement_type", "text"}
    for requirement in requirements:
        missing = sorted(key for key in required_keys if not requirement.get(key))
        if missing:
            notes.append(f"{requirement.get('requirement_id', 'unknown')} 缺少欄位：{', '.join(missing)}。")
    notes.extend([note for note in parser_notes if "未明確定義" not in note])
    return ("fail" if notes else "pass"), notes


def gate_c_status(
    cases: list[dict[str, Any]],
    coverage: dict[str, Any],
    requirements_by_id: dict[str, dict[str, Any]],
) -> tuple[str, list[str]]:
    notes: list[str] = []
    category_counts = Counter(case["category"] for case in cases)
    if len(cases) < 10:
        notes.append("case 數量少於 10。")
    for category, expected_count in {"positive": 3, "negative": 3, "edge": 2, "compliance": 2}.items():
        if category_counts.get(category, 0) < expected_count:
            notes.append(f"{category} case 少於 {expected_count}。")
    for case in cases:
        if not case["requirements_under_test"]:
            notes.append(f"{case['case_id']} 缺少 requirements_under_test。")

    covered_ids = {item["requirement_id"] for item in coverage["covered"]}
    covered_requirements = [requirements_by_id[requirement_id] for requirement_id in covered_ids]

    def has_covered(predicate: Any) -> bool:
        return any(predicate(requirement) for requirement in covered_requirements)

    if not has_covered(lambda requirement: requirement["requirement_type"] == "trigger"):
        notes.append("未覆蓋 trigger requirement。")
    if not any(case["category"] == "negative" for case in cases):
        notes.append("未覆蓋不觸發條件。")
    if not has_covered(lambda requirement: requirement["source_file"] == "references/report-templates.md"):
        notes.append("未覆蓋 report template requirement。")
    if not has_covered(lambda requirement: requirement["source_file"] == "references/review-workflow.md"):
        notes.append("未覆蓋 review workflow requirement。")
    if not has_covered(lambda requirement: requirement["source_file"] == "references/java-rules.md"):
        notes.append("未覆蓋 Java rules requirement。")
    edge_prompts = " ".join(case["prompt"] for case in cases if case["category"] == "edge")
    if "讀不到" not in edge_prompts and "工具" not in edge_prompts:
        notes.append("未覆蓋缺檔或工具不可用情境。")
    if not has_covered(lambda requirement: requirement["requirement_type"] == "must"):
        notes.append("未覆蓋至少一條 MUST requirement。")
    if not has_covered(lambda requirement: requirement["requirement_type"] == "must_not"):
        notes.append("未覆蓋至少一條 MUST NOT requirement。")

    return ("fail" if notes else "pass"), notes


def gate_d_status(
    validation_mode: str, results: list[dict[str, Any]], runtime_notes: list[str]
) -> tuple[str, list[str]]:
    notes: list[str] = []
    for result in results:
        if validation_mode == "runtime_validation":
            required_fields = ("command", "working_directory", "exit_code", "stdout", "stderr")
            missing = [field for field in required_fields if result.get(field) is None]
            if missing:
                notes.append(f"{result['case_id']} 的 runtime 欄位缺少：{', '.join(missing)}。")
        else:
            forbidden = ("command", "exit_code", "stdout", "stderr")
            present = [field for field in forbidden if result.get(field) is not None]
            if present:
                notes.append(f"{result['case_id']} 在 static_validation_only 下不應填寫：{', '.join(present)}。")
            if "runtime" in result["actual_behavior"].lower():
                notes.append(f"{result['case_id']} 在 static_validation_only 下宣稱 runtime 行為。")
    return ("fail" if notes else "pass"), notes


def gate_e_status(
    results: list[dict[str, Any]],
    summary: dict[str, Any],
) -> tuple[str, list[str]]:
    notes: list[str] = []
    skipped = sum(1 for result in results if result["reason"].lower().startswith("skip"))
    if skipped != 0:
        notes.append("不得把 skip 算作 pass；目前發現 skip。")
    passed = sum(1 for result in results if result["passed"])
    failed = len(results) - passed
    if summary["results"]["passed"] != passed or summary["results"]["failed"] != failed:
        notes.append("summary 數字與 JSONL 不一致。")
    output_files = summary["output_files"]
    for key in (
        "jsonl_results_relative",
        "jsonl_results_absolute",
        "requirements_coverage_relative",
        "requirements_coverage_absolute",
        "summary_relative",
        "summary_absolute",
        "readme_relative",
        "readme_absolute",
    ):
        if not output_files.get(key):
            notes.append(f"輸出路徑缺少 {key}。")
    return ("fail" if notes else "pass"), notes


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")


def validate_skill(args: argparse.Namespace) -> int:
    skill_root = resolve_skill_root(Path(args.skill_root))
    output_dir = (skill_root / args.output_dir).resolve() if not Path(args.output_dir).is_absolute() else Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    invocation_command = " ".join(shlex.quote(part) for part in [sys.executable, *sys.argv])

    source_manifest, source_texts, manifest_notes = build_source_manifest(skill_root)
    requirements, categories, parser_notes = parse_requirements(source_texts)
    cases, case_notes = build_cases(requirements, source_manifest)

    validation_mode = "static_validation_only"
    runtime_template: list[str] | None = None
    runtime_notes: list[str] = []
    if args.validation_mode == "runtime":
        runtime_template, runtime_reason = detect_runtime_command()
        if runtime_template is None:
            runtime_notes.append(runtime_reason or "runtime mode 不可用。")
        else:
            validation_mode = "runtime_validation"
    elif args.validation_mode == "auto":
        runtime_template, runtime_reason = detect_runtime_command()
        if runtime_template is None:
            runtime_notes.append(runtime_reason or "auto mode 降級為 static_validation_only。")
        else:
            validation_mode = "runtime_validation"
    else:
        runtime_notes.append("validation-mode=static，僅執行 static validation。")

    requirements_by_id = {item["requirement_id"]: item for item in requirements}

    results: list[dict[str, Any]] = []
    for case in cases:
        if validation_mode == "runtime_validation" and runtime_template is not None:
            (
                passed,
                actual_behavior,
                reason,
                command_text,
                working_directory,
                exit_code,
                stdout,
                stderr,
            ) = evaluate_runtime_case(case, runtime_template, skill_root)
        else:
            passed, actual_behavior, reason = evaluate_static_case(case, requirements_by_id)
            command_text = None
            working_directory = None
            exit_code = None
            stdout = None
            stderr = None

        results.append(
            {
                "case_id": case["case_id"],
                "category": case["category"],
                "prompt": case["prompt"],
                "expected_behavior": case["expected_behavior"],
                "actual_behavior": actual_behavior,
                "requirements_under_test": case["requirements_under_test"],
                "source_files_under_test": case["source_files_under_test"],
                "command": command_text,
                "working_directory": working_directory,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "passed": passed,
                "validation_mode": validation_mode,
                "reason": reason,
            }
        )

    coverage = build_coverage(requirements, results)
    coverage["notes"].extend(case_notes)
    coverage["notes"].extend(note for note in parser_notes if "未明確定義" in note)
    if validation_mode == "static_validation_only":
        coverage["notes"].extend(runtime_notes)

    gate_a, gate_a_notes = gate_a_status(source_manifest)
    gate_b, gate_b_notes = gate_b_status(requirements, parser_notes)
    gate_c, gate_c_notes = gate_c_status(cases, coverage, requirements_by_id)
    gate_d, gate_d_notes = gate_d_status(validation_mode, results, runtime_notes)

    jsonl_path = output_dir / "validation_results.jsonl"
    coverage_path = output_dir / "requirements_coverage.json"
    summary_path = output_dir / "validation_summary.json"
    manifest_path = output_dir / "spec_source_manifest.json"
    catalog_path = output_dir / "requirements_catalog.json"
    readme_path = skill_root / "skill_validation" / "README.md"

    passed_count = sum(1 for result in results if result["passed"])
    failed_count = len(results) - passed_count

    summary = {
        "working_directory": str(skill_root),
        "command": invocation_command,
        "exit_code": 0,
        "validation_mode": validation_mode,
        "gate_status": {
            "gate_a_spec_sources": gate_a,
            "gate_b_requirements": gate_b,
            "gate_c_case_coverage": gate_c,
            "gate_d_validation_mode": gate_d,
            "gate_e_result_honesty": "pending",
        },
        "results": {
            "passed": passed_count,
            "failed": failed_count,
            "skipped": 0,
        },
        "output_files": {
            "jsonl_results_relative": relative_to_root(jsonl_path, skill_root),
            "jsonl_results_absolute": str(jsonl_path),
            "requirements_coverage_relative": relative_to_root(coverage_path, skill_root),
            "requirements_coverage_absolute": str(coverage_path),
            "summary_relative": relative_to_root(summary_path, skill_root),
            "summary_absolute": str(summary_path),
            "readme_relative": relative_to_root(readme_path, skill_root),
            "readme_absolute": str(readme_path),
        },
        "coverage": {
            "covered_requirements": coverage["covered_requirements"],
            "total_requirements": coverage["total_requirements"],
            "coverage_ratio": coverage["coverage_ratio"],
        },
        "notes": manifest_notes + parser_notes + case_notes + runtime_notes + gate_a_notes + gate_b_notes + gate_c_notes + gate_d_notes,
    }

    gate_e, gate_e_notes = gate_e_status(results, summary)
    summary["gate_status"]["gate_e_result_honesty"] = gate_e
    summary["notes"].extend(gate_e_notes)

    write_jsonl(jsonl_path, results)
    write_json(coverage_path, coverage)
    write_json(
        manifest_path,
        {
            "skill_root": str(skill_root),
            "sources": source_manifest,
        },
    )
    write_json(
        catalog_path,
        {
            "requirements": requirements,
            **categories,
            "notes": parser_notes,
        },
    )
    write_json(summary_path, summary)
    return 0


def main() -> int:
    try:
        return validate_skill(parse_args())
    except Exception as exc:  # pragma: no cover - final safety net
        sys.stderr.write(f"skill validation failed: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
