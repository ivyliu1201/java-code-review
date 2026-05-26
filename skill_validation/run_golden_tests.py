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
import unicodedata
from pathlib import Path
from typing import Any


REQUIRED_SOURCES = [
    "SKILL.md",
    "references/report-templates.md",
    "references/review-workflow.md",
    "references/java-rules.md",
]

RUNTIME_ENV_KEY = "CODEX_RUNTIME_COMMAND"
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "from",
    "into",
    "must",
    "should",
    "java",
    "code",
    "review",
    "rule",
    "rules",
    "use",
    "using",
    "into",
    "then",
    "when",
    "避免",
    "必須",
    "應",
    "不要",
    "不得",
    "直接",
    "進行",
    "問題",
    "風險",
}
SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}
OUTPUT_SECTION_TITLES = (
    ("問題清單",),
    ("審查範圍",),
    ("開放問題",),
    ("剩餘風險",),
)
REQUIRED_FINDING_TABLE_HEADER = ("嚴重度", "標題", "規則", "檔案行號", "影響", "修正方向")
ALLOWED_CHINESE_SEVERITIES = {"嚴重", "主要", "次要", "建議", "無"}
MOJIBAKE_HINTS = ("Ã", "â", "ç", "å", "æ", "ï¼", "ï½")
NULL_LABELS = {"none", "無", "-", "n/a", "na"}
FINDING_SECTION_TITLES = {
    "findings",
    "問題清單",
    "審查結果",
    "問題發現",
    "問題摘要",
    "問題總覽",
    "問題彙總",
    "發現摘要",
    "detailed findings",
    "詳細問題",
}
NON_FINDING_SECTION_TITLES = {
    "review scope",
    "審查範圍",
    "current batch",
    "目前批次",
    "review ledger",
    "審查台帳",
    "batch summary",
    "批次摘要",
    "high priority findings",
    "高優先問題摘要",
    "progress",
    "進度",
    "open questions",
    "開放問題",
    "residual risks",
    "剩餘風險",
    "殘餘風險",
    "continuation prompt",
    "續跑提示",
}
CANONICAL_OUTPUT_SECTION_TITLES = {aliases[0].lower() for aliases in OUTPUT_SECTION_TITLES}
EXTRA_FORBIDDEN_OUTPUT_SECTION_TITLES = set()
FORBIDDEN_OUTPUT_SECTION_TITLES = set()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run golden tests for java-code-review skill.")
    parser.add_argument("--skill-root", default=".", help="Skill root directory.")
    parser.add_argument("--output-dir", required=True, help="Golden test output directory.")
    parser.add_argument(
        "--case-set",
        choices=("baseline", "holdout", "all"),
        default="baseline",
        help="Benchmark case set selection.",
    )
    parser.add_argument(
        "--validation-mode",
        choices=("auto", "runtime", "static"),
        default="auto",
        help="Validation mode selection.",
    )
    return parser.parse_args()


def read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_text_with_fallback(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "cp950", "big5", "gb18030"):
        try:
            text = data.decode(encoding)
            return normalize_runtime_text(text)
        except UnicodeDecodeError:
            continue
    return normalize_runtime_text(data.decode("utf-8", errors="replace"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")


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
            except Exception as exc:  # pragma: no cover
                item["read_status"] = "error"
                item["error"] = str(exc)
                notes.append(f"{relative_path} 讀取失敗：{exc}")
        else:
            notes.append(f"{relative_path} 缺失。")
        manifest.append(item)
    return manifest, source_texts, notes


def parse_rule_sections(java_rules_text: str) -> dict[str, str]:
    lines = java_rules_text.splitlines()
    sections: dict[str, list[str]] = {}
    current_rule_id: str | None = None

    for line in lines:
        match = re.match(r"^##\s+((?:[A-Z]|0)-\d+)\s+(.*)$", line)
        if match:
            current_rule_id = match.group(1)
            sections[current_rule_id] = [line]
            continue
        if current_rule_id is not None:
            if line.startswith("## "):
                current_rule_id = None
            else:
                sections[current_rule_id].append(line)

    return {rule_id: "\n".join(content).strip() for rule_id, content in sections.items()}


def extract_heading_section(markdown_text: str, heading: str) -> str:
    lines = markdown_text.splitlines()
    start_index: int | None = None
    start_level = 0

    for index, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if not match:
            continue
        title = match.group(2).strip()
        if title == heading:
            start_index = index
            start_level = len(match.group(1))
            break

    if start_index is None:
        return ""

    collected: list[str] = []
    for index in range(start_index, len(lines)):
        line = lines[index]
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if index > start_index and match and len(match.group(1)) <= start_level:
            break
        collected.append(line)
    return "\n".join(collected).strip()


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


def build_runtime_command(template: list[str], prompt: str, skill_root: Path, prompt_path: Path) -> list[str]:
    prompt_path.write_text(prompt, encoding="utf-8")
    command: list[str] = []
    replacements = {
        "{prompt}": prompt,
        "{prompt_file}": str(prompt_path),
        "{skill_root}": str(skill_root),
    }
    for part in template:
        updated = part
        for placeholder, value in replacements.items():
            updated = updated.replace(placeholder, value)
        command.append(updated)
    return command


def tokenize(text: str) -> set[str]:
    text = normalize_runtime_text(text)
    tokens: set[str] = set()
    for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[\u4e00-\u9fff]{2,}", text):
        lowered = token.lower()
        if lowered in STOPWORDS:
            continue
        tokens.add(lowered)
        if re.fullmatch(r"[\u4e00-\u9fff]{3,}", token):
            for index in range(len(token) - 1):
                tokens.add(token[index : index + 2].lower())
    return tokens


def normalize_runtime_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    if any(hint in normalized for hint in MOJIBAKE_HINTS):
        try:
            repaired = normalized.encode("latin1").decode("utf-8")
            normalized = unicodedata.normalize("NFKC", repaired)
        except UnicodeError:
            pass
    return normalized


def normalize_heading_token(text: str) -> str:
    token = normalize_runtime_text(text).strip()
    token = re.sub(r"^#+\s*", "", token)
    token = token.strip("*").strip()
    token = token.rstrip(":").strip()
    return token


def has_required_sections(stdout: str, required_groups: tuple[tuple[str, ...], ...]) -> bool:
    normalized = normalize_runtime_text(stdout)
    return all(any(alias in normalized for alias in aliases) for aliases in required_groups)


def extract_top_level_section_order(stdout: str) -> list[str]:
    sections: list[str] = []
    for raw_line in normalize_runtime_text(stdout).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        heading = normalize_heading_token(line)
        for aliases in OUTPUT_SECTION_TITLES:
            if heading in aliases:
                sections.append(aliases[0])
                break
    return sections


def has_required_section_order(stdout: str) -> bool:
    sections = extract_top_level_section_order(stdout)
    required = [aliases[0] for aliases in OUTPUT_SECTION_TITLES]
    cursor = 0
    for section in sections:
        if cursor < len(required) and section == required[cursor]:
            cursor += 1
    return cursor == len(required)


def first_content_line_is_problem_list(stdout: str) -> bool:
    for raw_line in normalize_runtime_text(stdout).splitlines():
        line = raw_line.strip()
        if line:
            return normalize_heading_token(line) == "問題清單"
    return False


def has_no_forbidden_sections(stdout: str) -> bool:
    return True


def has_required_finding_table_header(stdout: str) -> bool:
    normalized = normalize_runtime_text(stdout)
    for raw_line in normalized.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        if cells == REQUIRED_FINDING_TABLE_HEADER:
            return True
    return False


def finding_table_uses_chinese_severity(stdout: str) -> bool:
    normalized = normalize_runtime_text(stdout)
    header_seen = False
    for raw_line in normalized.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            if header_seen and line:
                break
            continue
        cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        if cells == REQUIRED_FINDING_TABLE_HEADER:
            header_seen = True
            continue
        if not header_seen or not cells or all(not cell or set(cell) <= {"-"} for cell in cells):
            continue
        severity = cells[0]
        if severity.lower() in {"major", "critical", "minor", "suggestions", "high", "medium", "low"}:
            return False
        if severity not in ALLOWED_CHINESE_SEVERITIES:
            return False
    return header_seen


def extract_rule_ids(text: str) -> set[str]:
    return {match.upper() for match in re.findall(r"\b([A-Z]-\d+)\b", text)}


def extract_filenames(text: str) -> set[str]:
    names = set(re.findall(r"([A-Za-z0-9_]+\.java)", text))
    return {name.lower() for name in names}


def parse_actual_findings(stdout: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    severity_map = {
        "Critical": "critical",
        "Major": "high",
        "Minor": "medium",
        "Suggestions": "low",
        "Must": "high",
        "Should": "medium",
        "嚴重": "critical",
        "主要": "high",
        "重大": "high",
        "次要": "medium",
        "建議": "low",
        "高": "high",
        "中": "medium",
        "中等": "medium",
        "低": "low",
    }
    current_severity: str | None = None
    current_finding: dict[str, Any] | None = None
    inside_finding_section = False
    table_headers: list[str] = []

    stdout = normalize_runtime_text(stdout)
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        heading = normalize_heading_token(line)
        heading_key = heading.lower()

        if heading_key in FINDING_SECTION_TITLES:
            inside_finding_section = True
            current_severity = None
            current_finding = None
            table_headers = []
            continue
        if heading_key in NON_FINDING_SECTION_TITLES:
            inside_finding_section = False
            current_severity = None
            current_finding = None
            table_headers = []
            continue
        if heading in severity_map:
            inside_finding_section = True
            current_severity = severity_map[heading]
            current_finding = None
            continue
        if not line:
            continue

        if line.startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            is_finding_table = (
                inside_finding_section
                or bool(table_headers)
                or bool(cells and cells[0].lower() in {"嚴重度", "嚴重程度", "severity"})
            )
            if not is_finding_table:
                continue
            if not cells or all(not cell or set(cell) <= {"-"} for cell in cells):
                continue
            if cells[0].lower() in {"嚴重度", "嚴重程度", "severity"}:
                inside_finding_section = True
                table_headers = [cell.lower() for cell in cells]
                continue
            severity_index = 0
            for severity_header in ("嚴重度", "嚴重程度", "severity"):
                if severity_header in table_headers:
                    severity_index = table_headers.index(severity_header)
                    break
            if severity_index >= len(cells):
                continue
            severity_value = severity_map.get(cells[severity_index])
            if severity_value and table_headers:
                def cell_for(*names: str) -> str:
                    for name in names:
                        key = name.lower()
                        if key in table_headers:
                            index = table_headers.index(key)
                            if index < len(cells):
                                return cells[index]
                    return ""

                title = cell_for("標題", "問題", "問題說明", "說明")
                rule = cell_for("規則")
                location = cell_for("檔案行號", "檔案與行號", "檔案:行號", "位置", "檔案")
                why = cell_for("影響", "問題", "問題說明", "說明")
                suggested_fix = cell_for("修正方向", "建議修正", "建議")
                if title.lower() in NULL_LABELS:
                    continue
                current_finding = {
                    "severity": severity_value,
                    "title": title,
                    "rule": rule,
                    "why": why,
                    "suggested_fix": suggested_fix,
                    "raw_lines": [line, location, *cells],
                }
                findings.append(current_finding)
                continue
            if severity_value and len(cells) >= 6:
                title = cells[1]
                if title.lower() in NULL_LABELS:
                    continue
                current_finding = {
                    "severity": severity_value,
                    "title": title,
                    "rule": cells[2],
                    "why": cells[4],
                    "suggested_fix": cells[5],
                    "raw_lines": [line, cells[3]],
                }
                findings.append(current_finding)
            elif severity_value and len(cells) >= 5:
                title = cells[3]
                if title.lower() in NULL_LABELS:
                    continue
                rule = cells[2] if extract_rule_ids(cells[2]) else ""
                current_finding = {
                    "severity": severity_value,
                    "title": title,
                    "rule": rule,
                    "why": cells[3],
                    "suggested_fix": cells[4],
                    "raw_lines": [line, *cells],
                }
                findings.append(current_finding)
            continue

        finding_match = re.match(r"^(\d+\.|-)\s+(.*)$", line)
        inline_severity_match = re.match(r"^(\d+\.|-)\s+`?([A-Za-z\u4e00-\u9fff]+)`?\s*(.*)$", line)
        if inline_severity_match:
            severity_token = inline_severity_match.group(2)
            inline_severity = severity_map.get(severity_token)
            if inline_severity:
                remainder = inline_severity_match.group(3).strip()
                candidate_title = remainder or severity_token
                current_finding = {
                    "severity": inline_severity,
                    "title": candidate_title,
                    "rule": " ".join(sorted(extract_rule_ids(candidate_title))),
                    "why": "",
                    "suggested_fix": "",
                    "raw_lines": [line],
                }
                findings.append(current_finding)
                current_severity = inline_severity
                continue
        if finding_match and current_severity is not None:
            candidate_title = finding_match.group(2).strip()
            if candidate_title.lower() in NULL_LABELS:
                continue
            current_finding = {
                "severity": current_severity,
                "title": candidate_title,
                "rule": "",
                "why": "",
                "suggested_fix": "",
                "raw_lines": [line],
            }
            findings.append(current_finding)
            continue

        if current_finding is None:
            continue

        current_finding["raw_lines"].append(line)
        if line.startswith(("Rule:", "規則:")):
            current_finding["rule"] = line.partition(":")[2].strip()
        elif line.startswith(("Why:", "影響:")):
            current_finding["why"] = line.partition(":")[2].strip()
        elif line.startswith(("Suggested fix:", "修正方向:")):
            current_finding["suggested_fix"] = line.partition(":")[2].strip()

    return findings


def is_template_compliant(stdout: str) -> bool:
    return (
        has_required_sections(stdout, OUTPUT_SECTION_TITLES)
        and has_required_finding_table_header(stdout)
        and finding_table_uses_chinese_severity(stdout)
    )


def is_workflow_compliant(stdout: str) -> bool:
    required_terms = (
        ("審查範圍",),
        ("已審查檔案",),
        ("開放問題",),
        ("剩餘風險", "殘餘風險"),
    )
    return has_required_sections(stdout, required_terms)


def compare_finding(expected: dict[str, Any], actual: dict[str, Any]) -> tuple[bool, str]:
    expected_rule_ids = {expected["rule_id"].upper()}
    actual_rule_ids = extract_rule_ids(" ".join([actual.get("title", ""), actual.get("rule", ""), actual.get("why", "")]))
    expected_filename = expected.get("expected_filename", "").lower()
    actual_filenames = extract_filenames(" ".join(actual.get("raw_lines", [])))

    issue_expected = tokenize(expected["expected_issue"])
    issue_actual = tokenize(" ".join([actual.get("title", ""), actual.get("why", ""), actual.get("rule", "")]))
    evidence_expected = tokenize(expected["expected_evidence"])
    evidence_actual = tokenize(" ".join(actual.get("raw_lines", [])))
    recommendation_expected = tokenize(expected["expected_recommendation"])
    recommendation_actual = tokenize(" ".join([actual.get("suggested_fix", ""), *actual.get("raw_lines", [])]))

    rule_match = bool(expected_rule_ids & actual_rule_ids)
    file_match = not expected_filename or not actual_filenames or expected_filename in actual_filenames
    issue_match = bool(issue_expected & issue_actual)
    evidence_match = bool(evidence_expected & evidence_actual)
    recommendation_match = bool(recommendation_expected & recommendation_actual)

    expected_rank = SEVERITY_RANK[expected["severity"]]
    actual_rank = SEVERITY_RANK.get(actual["severity"], 0)
    severity_ok = True
    if expected["severity"] in {"critical", "high"} and actual_rank < expected_rank:
        severity_ok = False

    semantic_match = file_match and issue_match and evidence_match and recommendation_match and severity_ok
    passed = semantic_match
    reason_parts = []
    if not file_match:
        reason_parts.append("file 未對齊")
    if not issue_match:
        reason_parts.append("issue 未對齊")
    if not evidence_match:
        reason_parts.append("evidence 未對齊")
    if not recommendation_match:
        reason_parts.append("recommendation 未對齊")
    if not severity_ok:
        reason_parts.append("severity 被低估")
    if semantic_match and not rule_match:
        reason_parts.append("rule id 未對齊")

    return passed, "、".join(reason_parts) if reason_parts else "matched"


def detect_must_not_violations(actual_findings: list[dict[str, Any]], forbidden_labels: list[str]) -> list[str]:
    violations: list[str] = []
    for actual in actual_findings:
        combined = " ".join(
            [
                actual.get("title", ""),
                actual.get("rule", ""),
                actual.get("why", ""),
                actual.get("suggested_fix", ""),
            ]
        ).lower()
        for label in forbidden_labels:
            if label.lower() in combined:
                violations.append(label)
    return violations


def build_baseline_case_specs() -> list[dict[str, Any]]:
    return [
        {
            "golden_case_id": "security-01",
            "category": "security",
            "java_file": "SensitiveProfileService.java",
            "java_source": """package com.example.profile;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SensitiveProfileService {
    private static final Logger log = LoggerFactory.getLogger(SensitiveProfileService.class);

    public UserProfileResponse getProfile(User user) {
        log.info("profile loaded, user={}", user);
        return new UserProfileResponse(
                user.getName(),
                user.getMobile(),
                user.getEmail(),
                user.getIdNo(),
                user.getCardNo());
    }
}
""",
            "must_not_findings": ["命名規則違反", "常數規則違反"],
            "source_rules_under_test": ["H-2"],
            "expected_findings": [
                {
                    "rule_id": "H-2",
                    "severity": "high",
                    "expected_issue": "直接回傳完整敏感資料，沒有做最小化與脫敏。",
                    "expected_evidence": "UserProfileResponse getMobile getEmail getIdNo getCardNo",
                    "expected_recommendation": "不要直接回傳完整敏感欄位，改為最小化欄位與遮罩後 DTO。",
                },
                {
                    "rule_id": "H-2",
                    "severity": "high",
                    "expected_issue": "直接把完整 user 物件寫入日誌，沒有做脫敏。",
                    "expected_evidence": "log.info user",
                    "expected_recommendation": "避免記錄完整 user object，改記 userId 或脫敏後欄位。",
                }
            ],
        },
        {
            "golden_case_id": "null-safety-01",
            "category": "null_safety",
            "java_file": "OrderStatusChecker.java",
            "java_source": """package com.example.order;

public class OrderStatusChecker {
    public boolean isPaid(Order order) {
        return order.getStatus().equals("PAID");
    }
}
""",
            "must_not_findings": ["SQL injection", "交易邊界錯誤"],
            "source_rules_under_test": ["B-1"],
            "expected_findings": [
                {
                    "rule_id": "B-1",
                    "severity": "medium",
                    "expected_issue": "可能為 null 的值主動呼叫 equals，存在 NullPointerException 風險。",
                    "expected_evidence": "order.getStatus().equals(\"PAID\")",
                    "expected_recommendation": "改用常量發起 equals，例如 \"PAID\".equals(order.getStatus())，必要時補 null guard。",
                }
            ],
        },
        {
            "golden_case_id": "transaction-01",
            "category": "transaction",
            "java_file": "CheckoutService.java",
            "java_source": """package com.example.checkout;

import org.springframework.transaction.annotation.Transactional;

public class CheckoutService {
    private final OrderRepository orderRepository;
    private final PaymentClient paymentClient;
    private final AuditRepository auditRepository;

    public CheckoutService(OrderRepository orderRepository, PaymentClient paymentClient, AuditRepository auditRepository) {
        this.orderRepository = orderRepository;
        this.paymentClient = paymentClient;
        this.auditRepository = auditRepository;
    }

    @Transactional
    public void completeCheckout(CheckoutRequest request) {
        orderRepository.save(request.toOrder());
        paymentClient.charge(request.getPaymentToken(), request.getAmount());
        auditRepository.save(AuditLog.success(request.getOrderId()));
    }
}
""",
            "must_not_findings": ["缺少 @Transactional", "命名規則違反"],
            "source_rules_under_test": ["L-1"],
            "expected_findings": [
                {
                    "rule_id": "L-1",
                    "severity": "high",
                    "expected_issue": "在 @Transactional 交易內直接呼叫外部支付系統，可能破壞交易一致性。",
                    "expected_evidence": "@Transactional paymentClient.charge",
                    "expected_recommendation": "把外部呼叫移出本地交易邊界，或改用可補償的非同步 / outbox 設計。",
                }
            ],
        },
        {
            "golden_case_id": "performance-01",
            "category": "performance",
            "java_file": "OrderQueryService.java",
            "java_source": """package com.example.query;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OrderQueryService {
    private static final Logger log = LoggerFactory.getLogger(OrderQueryService.class);
    private final ObjectMapper objectMapper = new ObjectMapper();

    public OrderResponse query(OrderResponse response) throws JsonProcessingException {
        log.debug("response=" + objectMapper.writeValueAsString(response));
        return response;
    }
}
""",
            "must_not_findings": ["NullPointerException 風險", "交易邊界錯誤"],
            "source_rules_under_test": ["F-3"],
            "expected_findings": [
                {
                    "rule_id": "F-3",
                    "severity": "medium",
                    "expected_issue": "高頻路徑使用無條件字串拼接與序列化日誌，會造成不必要的效能成本。",
                    "expected_evidence": "log.debug(\"response=\" + objectMapper.writeValueAsString(response))",
                    "expected_recommendation": "改用參數化日誌，若需要昂貴序列化則先用 log level guard。",
                }
            ],
        },
        {
            "golden_case_id": "maintainability-01",
            "category": "maintainability",
            "java_file": "OrderApplicationService.java",
            "java_source": """package com.example.application;

public class OrderApplicationService {
    public OrderResult submitOrder(CreateOrderRequest request) {
        if (request == null || request.getUserId() == null || request.getItems() == null || request.getItems().isEmpty()) {
            throw new IllegalArgumentException("bad request");
        }
        User user = userRepository.findById(request.getUserId());
        if (user == null) {
            throw new IllegalStateException("user not found");
        }
        Order order = new Order();
        order.setUserId(user.getId());
        order.setAddress(request.getAddress());
        order.setItems(request.getItems());
        order.calculateAmount();
        orderRepository.save(order);
        inventoryService.reserve(order.getItems());
        couponService.consume(request.getCouponId());
        emailService.sendCreatedEmail(user.getEmail(), order.getId());
        auditService.record("order created", user.getId(), order.getId());
        return new OrderResult(order.getId(), order.getAmount());
    }

    private UserRepository userRepository;
    private OrderRepository orderRepository;
    private InventoryService inventoryService;
    private CouponService couponService;
    private EmailService emailService;
    private AuditService auditService;
}
""",
            "must_not_findings": ["敏感資料外洩", "SQL injection"],
            "source_rules_under_test": ["B-5"],
            "expected_findings": [
                {
                    "rule_id": "B-5",
                    "severity": "medium",
                    "expected_issue": "單一方法同時處理驗證、查詢、組裝、持久化、通知與稽核，違反單一職責。",
                    "expected_evidence": "submitOrder validation findById save reserve consume sendCreatedEmail record",
                    "expected_recommendation": "拆分成 validation、載入使用者、建立訂單、持久化、通知與稽核等明確方法。",
                }
            ],
        },
    ]


def build_holdout_case_specs() -> list[dict[str, Any]]:
    return [
        {
            "golden_case_id": "security-holdout-01",
            "category": "security",
            "java_file": "SessionCacheService.java",
            "java_source": """package com.example.session;

public class SessionCacheService {
    private final CacheClient cacheClient;

    public SessionCacheService(CacheClient cacheClient) {
        this.cacheClient = cacheClient;
    }

    public void cacheSession(UserSession session) {
        cacheClient.put(
                "session:" + session.getUserId(),
                new SessionSnapshot(
                        session.getUserId(),
                        session.getEmail(),
                        session.getCardNo(),
                        session.getAccessToken()));
    }
}
""",
            "must_not_findings": ["命名規則違反", "常數規則違反"],
            "source_rules_under_test": ["M-4"],
            "expected_findings": [
                {
                    "rule_id": "M-4",
                    "severity": "high",
                    "expected_issue": "Cache 中直接存放完整敏感資料與 access token，缺少最小化與保護。",
                    "expected_evidence": "cacheClient.put SessionSnapshot getEmail getCardNo getAccessToken",
                    "expected_recommendation": "不要把完整敏感資料與 token 直接放進 cache，只保留必要欄位，必要時改存脫敏值或短期識別資訊。",
                }
            ],
        },
        {
            "golden_case_id": "null-safety-holdout-01",
            "category": "null_safety",
            "java_file": "MemberLevelChecker.java",
            "java_source": """package com.example.member;

public class MemberLevelChecker {
    public boolean isVip(Member member) {
        return member.getLevel().equals("VIP");
    }
}
""",
            "must_not_findings": ["SQL injection", "交易邊界錯誤"],
            "source_rules_under_test": ["B-1"],
            "expected_findings": [
                {
                    "rule_id": "B-1",
                    "severity": "medium",
                    "expected_issue": "可能為 null 的值主動呼叫 equals，存在 NullPointerException 風險。",
                    "expected_evidence": "member.getLevel().equals(\"VIP\")",
                    "expected_recommendation": "改用常量發起 equals，例如 \"VIP\".equals(member.getLevel())，必要時補 null guard。",
                }
            ],
        },
        {
            "golden_case_id": "transaction-holdout-01",
            "category": "transaction",
            "java_file": "CouponGrantService.java",
            "java_source": """package com.example.coupon;

public class CouponGrantService {
    private final CouponClient couponClient;
    private final GrantLogRepository grantLogRepository;

    public CouponGrantService(CouponClient couponClient, GrantLogRepository grantLogRepository) {
        this.couponClient = couponClient;
        this.grantLogRepository = grantLogRepository;
    }

    public void grantCoupon(GrantCouponRequest request) {
        couponClient.issue(request.getUserId(), request.getCouponCode());
        grantLogRepository.save(GrantLog.success(
                request.getRequestId(),
                request.getUserId(),
                request.getCouponCode()));
    }
}
""",
            "must_not_findings": ["缺少 @Transactional", "命名規則違反"],
            "source_rules_under_test": ["J-6"],
            "expected_findings": [
                {
                    "rule_id": "J-6",
                    "severity": "high",
                    "expected_issue": "不可重複執行的發券流程看不到冪等設計，重試時可能重複發券。",
                    "expected_evidence": "grantCoupon couponClient.issue request.getRequestId grantLogRepository.save",
                    "expected_recommendation": "在發券邊界使用 requestId 或其他 idempotency key，搭配唯一約束、狀態檢查或 duplicate handling，避免重複發券。",
                }
            ],
        },
        {
            "golden_case_id": "performance-holdout-01",
            "category": "performance",
            "java_file": "BatchSyncService.java",
            "java_source": """package com.example.sync;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BatchSyncService {
    private static final Logger log = LoggerFactory.getLogger(BatchSyncService.class);
    private final ObjectMapper objectMapper = new ObjectMapper();

    public void sync(List<Order> orders) throws JsonProcessingException {
        for (Order order : orders) {
            log.info("sync payload=" + objectMapper.writeValueAsString(order));
        }
    }
}
""",
            "must_not_findings": ["NullPointerException 風險", "交易邊界錯誤"],
            "source_rules_under_test": ["F-3"],
            "expected_findings": [
                {
                    "rule_id": "F-3",
                    "severity": "medium",
                    "expected_issue": "迴圈中的無條件字串拼接與序列化日誌會造成不必要的效能成本。",
                    "expected_evidence": "for log.info objectMapper.writeValueAsString(order)",
                    "expected_recommendation": "改用參數化日誌，若序列化成本高則加 log level guard，避免在迴圈中每次都做昂貴字串組裝。",
                }
            ],
        },
        {
            "golden_case_id": "maintainability-holdout-01",
            "category": "maintainability",
            "java_file": "UserController.java",
            "java_source": """package com.example.user;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class UserController {
    private final UserRepository userRepository;

    public UserController(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @PostMapping("/users")
    public UserEntity create(@RequestBody UserEntity user) {
        return userRepository.save(user);
    }
}
""",
            "must_not_findings": ["敏感資料外洩", "SQL injection"],
            "source_rules_under_test": ["L-3"],
            "expected_findings": [
                {
                    "rule_id": "L-3",
                    "severity": "high",
                    "expected_issue": "Request DTO、Response DTO 與 Entity 直接混用，會讓 API 邊界與資料模型耦合。",
                    "expected_evidence": "@RequestBody UserEntity return userRepository.save(user)",
                    "expected_recommendation": "改用明確的 CreateUserRequest 與 UserResponse，避免直接接收或回傳 Entity。",
                }
            ],
        },
    ]


def build_golden_case_specs(case_set: str) -> list[dict[str, Any]]:
    baseline_cases = build_baseline_case_specs()
    holdout_cases = build_holdout_case_specs()
    if case_set == "baseline":
        return baseline_cases
    if case_set == "holdout":
        return holdout_cases
    return baseline_cases + holdout_cases


def build_prompt(case: dict[str, Any], relative_java_path: str) -> str:
    compact_template = case.get("template_excerpt", "").strip()
    compact_workflow = case.get("workflow_excerpt", "").strip()
    rule_excerpt = case.get("rule_excerpt", "").strip()
    return (
        "請依照 java-code-review skill 與本地 Java 規則進行正式 code review。\n"
        "這是一個 single-file benchmark。你不得要求額外輸入、不得要求 git diff、不得要求檢查其他檔案、不得先回覆無法 review。\n"
        "你只能根據此 prompt 內提供的規則摘要、模板摘要、workflow 摘要與 inline Java source 完成 review。\n"
        "即使你無法讀取 workspace 或 shell，也必須直接完成 review，不可把執行環境問題當成結論。\n"
        "要求：\n"
        "1. 使用繁體中文。\n"
        "2. 套用此 prompt 內嵌的本地規則摘要；這些摘要已由 references/java-rules.md 讀出。\n"
        "3. 套用此 prompt 內嵌的模板與 workflow 摘要；這些摘要已由 references/report-templates.md 與 references/review-workflow.md 讀出。\n"
        "4. 不要說明你需要更多上下文；這個 Java 檔案就是完整 review 對象。\n"
        "5. 請附檔案與行號，檔案只使用提供的路徑。\n"
        "6. 只 review 這一個檔案，不得引用或審查其他 Java 檔案。\n"
        "7. 以 Compact Review Mode 輸出。\n"
        "8. 正式報告優先使用中文表格；若有相關 finding，請盡量在規則欄標出精確 rule id。\n"
        f"9. 只 review 這個檔案：{relative_java_path}\n\n"
        "本地規則摘要：\n"
        f"{rule_excerpt}\n\n"
        "Compact Review Mode workflow 摘要：\n"
        f"{compact_workflow}\n\n"
        "Compact 正式模板摘要：\n"
        f"{compact_template}\n\n"
        f"Java source:\n```java\n{case['java_source']}\n```\n"
    )


def generate_cases(
    skill_root: Path,
    golden_cases_dir: Path,
    rule_sections: dict[str, str],
    source_texts: dict[str, str],
    case_set: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    notes: list[str] = []
    cases = build_golden_case_specs(case_set)
    compact_template = extract_heading_section(
        source_texts.get("references/report-templates.md", ""),
        "Compact 正式 Review 模板",
    )
    compact_workflow = extract_heading_section(
        source_texts.get("references/review-workflow.md", ""),
        "Compact Review Mode",
    )

    for case in cases:
        for expected in case["expected_findings"]:
            rule_id = expected["rule_id"]
            if rule_id not in rule_sections:
                notes.append(f"{case['golden_case_id']} 找不到對應 rule id: {rule_id}")
            expected["expected_filename"] = case["java_file"].lower()
        rule_ids = case["source_rules_under_test"]
        case["rule_excerpt"] = "\n\n".join(rule_sections[rule_id] for rule_id in rule_ids if rule_id in rule_sections)
        case["template_excerpt"] = compact_template
        case["workflow_excerpt"] = compact_workflow
        java_path = golden_cases_dir / case["java_file"]
        java_path.write_text(case["java_source"], encoding="utf-8")
        case["java_file_absolute"] = str(java_path)
        case["java_file_relative"] = relative_to_root(java_path, skill_root)
        case["prompt"] = build_prompt(case, case["java_file_relative"])

    return cases, notes


def evaluate_static_case(case: dict[str, Any], rule_sections: dict[str, str]) -> tuple[bool, str]:
    if not case["expected_findings"]:
        return False, "case 缺少 expected_findings。"
    if not case["must_not_findings"]:
        return False, "case 缺少 must_not_findings。"

    for expected in case["expected_findings"]:
        required_keys = (
            "rule_id",
            "severity",
            "expected_issue",
            "expected_evidence",
            "expected_recommendation",
        )
        if any(not expected.get(key) for key in required_keys):
            return False, f"expected finding 缺少欄位：{expected}"
        if expected["rule_id"] not in rule_sections:
            return False, f"expected finding 的 rule_id 無法對應 java-rules.md：{expected['rule_id']}"

    return True, "static mode 僅驗證 case 結構、rule 對應與比對邏輯存在，未實際驗證 review 準確度。"


def evaluate_runtime_case(
    case: dict[str, Any], runtime_template: list[str], case_workspace: Path, prompt_path: Path
) -> dict[str, Any]:
    command_list = build_runtime_command(runtime_template, case["prompt"], case_workspace, prompt_path)
    last_message_path = prompt_path.with_name(f"{case['golden_case_id']}_last_message.txt")
    command_name = Path(command_list[0]).name.lower()
    if command_name.startswith("codex") and "--output-last-message" not in command_list and "-o" not in command_list:
        command_list.extend(["--output-last-message", str(last_message_path), "--color", "never"])
    timeout_seconds = 300
    try:
        completed = subprocess.run(
            command_list,
            cwd=case_workspace,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
        stdout_text = normalize_runtime_text(completed.stdout)
        if last_message_path.exists():
            stdout_text = read_text_with_fallback(last_message_path)
        exit_code = completed.returncode
        stderr_text = normalize_runtime_text(completed.stderr)
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout_text = read_text_with_fallback(last_message_path) if last_message_path.exists() else normalize_runtime_text(exc.stdout or "")
        stderr_text = normalize_runtime_text(exc.stderr or "") + f"\nTimeoutExpired after {timeout_seconds} seconds."
        exit_code = -1
        timed_out = True

    actual_findings = parse_actual_findings(stdout_text)
    matched_findings = []
    missed_findings = []
    used_actual_indexes: set[int] = set()
    rule_id_alignment_issues: list[dict[str, Any]] = []

    for expected in case["expected_findings"]:
        matched_indexes: list[int] = []
        best_reason = "沒有命中對應 finding。"
        for index, actual in enumerate(actual_findings):
            passed, reason = compare_finding(expected, actual)
            if passed:
                matched_indexes.append(index)
                used_actual_indexes.add(index)
            best_reason = reason
        if matched_indexes:
            actual_titles = [actual_findings[index].get("title", "") for index in matched_indexes]
            matched_rules = [
                sorted(
                    extract_rule_ids(
                        " ".join(
                            [
                                actual_findings[index].get("title", ""),
                                actual_findings[index].get("rule", ""),
                                actual_findings[index].get("why", ""),
                            ]
                        )
                    )
                )
                for index in matched_indexes
            ]
            if not any(expected["rule_id"] in rules for rules in matched_rules):
                rule_id_alignment_issues.append(
                    {
                        "rule_id": expected["rule_id"],
                        "expected_issue": expected["expected_issue"],
                        "actual_titles": actual_titles,
                    }
                )
            matched_findings.append(
                {
                    "rule_id": expected["rule_id"],
                    "expected_issue": expected["expected_issue"],
                    "actual_titles": actual_titles,
                }
            )
        else:
            missed_findings.append(
                {
                    "rule_id": expected["rule_id"],
                    "expected_issue": expected["expected_issue"],
                    "reason": best_reason,
                    "severity": expected["severity"],
                }
            )

    unexpected_findings = [
        actual_findings[index]
        for index in range(len(actual_findings))
        if index not in used_actual_indexes
    ]
    must_not_violations = detect_must_not_violations(actual_findings, case["must_not_findings"])
    template_compliance = is_template_compliant(stdout_text)
    workflow_compliance = is_workflow_compliant(stdout_text)
    precision = 0.0 if not actual_findings else len(matched_findings) / len(actual_findings)
    recall = 0.0 if not case["expected_findings"] else len(matched_findings) / len(case["expected_findings"])
    quality_pass = (
        exit_code == 0
        and not missed_findings
        and not must_not_violations
    )
    scope_pass = True
    format_pass = template_compliance and workflow_compliance
    overall_pass = quality_pass and scope_pass and format_pass

    if timed_out:
        reason = f"runtime mode 執行逾時，case 已記錄為失敗；timeout={timeout_seconds}s。"
    elif not actual_findings:
        reason = "runtime mode 已執行，但沒有解析到 actual findings；precision 不代表真實準確度。"
    elif overall_pass:
        reason = "runtime mode 比對通過。"
    elif quality_pass and scope_pass and not format_pass:
        reason = "runtime mode 品質比對通過，但輸出格式或 workflow 訊號不符合契約。"
    elif not quality_pass and scope_pass and format_pass:
        reason = "runtime mode 格式符合契約，但 finding 品質比對未通過。"
    else:
        reason = "runtime mode 執行完成，但 quality / scope / format 訊號未完全符合。"

    return {
        "actual_findings": actual_findings,
        "matched_findings": matched_findings,
        "missed_findings": missed_findings,
        "unexpected_findings": unexpected_findings,
        "rule_id_alignment_issues": rule_id_alignment_issues,
        "must_not_violations": must_not_violations,
        "template_compliance": template_compliance,
        "workflow_compliance": workflow_compliance,
        "quality_pass": quality_pass,
        "scope_pass": scope_pass,
        "format_pass": format_pass,
        "overall_pass": overall_pass,
        "precision_estimate": round(precision, 4),
        "recall_estimate": round(recall, 4),
        "command": subprocess.list2cmdline(command_list),
        "working_directory": str(case_workspace),
        "exit_code": exit_code,
        "stdout": stdout_text,
        "stderr": stderr_text,
        "passed": overall_pass,
        "reason": reason,
    }


def gate_a_status(source_manifest: list[dict[str, Any]], notes: list[str]) -> tuple[str, list[str]]:
    issues: list[str] = []
    skill_item = next((item for item in source_manifest if item["source_file"] == "SKILL.md"), None)
    rules_item = next((item for item in source_manifest if item["source_file"] == "references/java-rules.md"), None)

    if not skill_item or not skill_item["exists"]:
        issues.append("SKILL.md 缺失。")
    if not rules_item or not rules_item["exists"]:
        issues.append("references/java-rules.md 缺失。")
    for relative_path in ("references/report-templates.md", "references/review-workflow.md"):
        item = next((entry for entry in source_manifest if entry["source_file"] == relative_path), None)
        if item and not item["exists"] and not any(relative_path in note for note in notes):
            issues.append(f"{relative_path} 缺失但 notes 未標記。")
    for item in source_manifest:
        if item["exists"] and item["read_status"] != "read":
            issues.append(f"{item['source_file']} 讀取狀態為 {item['read_status']}。")

    return ("fail" if issues else "pass"), issues


def gate_b_status(cases: list[dict[str, Any]], rule_sections: dict[str, str]) -> tuple[str, list[str]]:
    issues: list[str] = []
    categories = {case["category"] for case in cases}
    required_categories = {"security", "null_safety", "performance", "maintainability"}
    if len(cases) < 5:
        issues.append("golden cases 少於 5 個。")
    if not required_categories.issubset(categories):
        issues.append("缺少 security、null_safety、performance 或 maintainability 類別。")
    if not ({"transaction"} & categories or {"resource_handling"} & categories):
        issues.append("缺少 transaction 或 resource_handling 類別。")

    for case in cases:
        if not case["java_source"]:
            issues.append(f"{case['golden_case_id']} 沒有由腳本產生 Java 測資。")
        if not case["expected_findings"]:
            issues.append(f"{case['golden_case_id']} 沒有 expected finding。")
        if not case["must_not_findings"]:
            issues.append(f"{case['golden_case_id']} 沒有 must_not finding。")
        for expected in case["expected_findings"]:
            for key in ("expected_issue", "expected_evidence", "severity", "expected_recommendation"):
                if not expected.get(key):
                    issues.append(f"{case['golden_case_id']} 的 expected finding 缺少 {key}。")
            if expected["rule_id"] not in rule_sections:
                issues.append(f"{case['golden_case_id']} 的 rule_id {expected['rule_id']} 無法對應 java-rules.md。")

    return ("fail" if issues else "pass"), issues


def gate_c_status(validation_mode: str, results: list[dict[str, Any]]) -> tuple[str, list[str]]:
    issues: list[str] = []
    for result in results:
        if validation_mode == "runtime_validation":
            for key in ("command", "working_directory", "exit_code", "stdout", "stderr"):
                if result[key] is None:
                    issues.append(f"{result['golden_case_id']} 的 runtime 欄位缺少 {key}。")
        else:
            for key in ("command", "exit_code", "stdout", "stderr"):
                if result[key] is not None:
                    issues.append(f"{result['golden_case_id']} 在 static mode 不應填寫 {key}。")
            if "準確度" in result["reason"] and "未實際驗證" not in result["reason"]:
                issues.append(f"{result['golden_case_id']} 在 static mode 不得宣稱已驗證 review 準確度。")

    return ("fail" if issues else "pass"), issues


def gate_d_status(validation_mode: str, results: list[dict[str, Any]]) -> tuple[str, list[str]]:
    issues: list[str] = []
    if validation_mode == "runtime_validation":
        for result in results:
            if result["precision_estimate"] == 1.0 and not result["actual_findings"]:
                issues.append(f"{result['golden_case_id']} 無 actual findings 卻偽造 precision=1.0。")
            for missed in result["missed_findings"]:
                if missed["severity"] in {"critical", "high"} and result.get("quality_pass", result["passed"]):
                    issues.append(f"{result['golden_case_id']} 漏掉 high/critical finding 卻仍判定通過。")
    else:
        for result in results:
            if result["template_compliance"] or result["workflow_compliance"]:
                issues.append(f"{result['golden_case_id']} 在 static mode 不得宣稱 template/workflow 已驗證。")
            if "未實際驗證" not in result["reason"]:
                issues.append(f"{result['golden_case_id']} 在 static mode 未說明 Gate D 只檢查比對邏輯存在。")

    return ("fail" if issues else "pass"), issues


def gate_e_status(summary: dict[str, Any], results: list[dict[str, Any]]) -> tuple[str, list[str]]:
    issues: list[str] = []
    passed = sum(1 for result in results if result["passed"])
    failed = len(results) - passed
    quality_passed = sum(1 for result in results if result.get("quality_pass", result["passed"]))
    scope_passed = sum(1 for result in results if result.get("scope_pass", True))
    format_passed = sum(1 for result in results if result.get("format_pass", result["passed"]))
    overall_passed = sum(1 for result in results if result.get("overall_pass", result["passed"]))

    if summary["passed_golden_cases"] != passed or summary["failed_golden_cases"] != failed:
        issues.append("summary 數字與 JSONL 不一致。")
    if summary.get("quality_passed_golden_cases") != quality_passed:
        issues.append("summary quality_passed_golden_cases 與 JSONL 不一致。")
    if "scope_passed_golden_cases" in summary and summary.get("scope_passed_golden_cases") != scope_passed:
        issues.append("summary scope_passed_golden_cases 與 JSONL 不一致。")
    if summary.get("format_passed_golden_cases") != format_passed:
        issues.append("summary format_passed_golden_cases 與 JSONL 不一致。")
    if summary.get("overall_passed_golden_cases") != overall_passed:
        issues.append("summary overall_passed_golden_cases 與 JSONL 不一致。")
    if summary.get("skipped_golden_cases", 0) != 0:
        issues.append("不得把 skip 算作 pass。")
    for key in (
        "golden_results_relative",
        "golden_results_absolute",
        "golden_summary_relative",
        "golden_summary_absolute",
        "readme_relative",
        "readme_absolute",
    ):
        if not summary["output_files"].get(key):
            issues.append(f"輸出路徑缺少 {key}。")

    return ("fail" if issues else "pass"), issues


def run(args: argparse.Namespace) -> int:
    skill_root = resolve_skill_root(Path(args.skill_root))
    output_dir = (skill_root / args.output_dir).resolve() if not Path(args.output_dir).is_absolute() else Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    golden_cases_dir = (skill_root / "skill_validation" / "golden_cases").resolve()
    golden_cases_dir.mkdir(parents=True, exist_ok=True)
    case_workspaces_dir = (output_dir / "case_workspaces").resolve()
    case_workspaces_dir.mkdir(parents=True, exist_ok=True)

    invocation_command = " ".join(shlex.quote(part) for part in [sys.executable, *sys.argv])

    source_manifest, source_texts, manifest_notes = build_source_manifest(skill_root)
    java_rules_text = source_texts.get("references/java-rules.md", "")
    rule_sections = parse_rule_sections(java_rules_text) if java_rules_text else {}
    cases, case_notes = generate_cases(skill_root, golden_cases_dir, rule_sections, source_texts, args.case_set)

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

    results: list[dict[str, Any]] = []
    for case in cases:
        case_workspace = case_workspaces_dir / case["golden_case_id"]
        case_workspace.mkdir(parents=True, exist_ok=True)
        case_java_path = case_workspace / case["java_file"]
        case_java_path.write_text(case["java_source"], encoding="utf-8")
        prompt_path = case_workspace / "runtime_prompt.txt"
        case_runtime_path = relative_to_root(case_java_path, case_workspace)
        if validation_mode == "runtime_validation" and runtime_template is not None:
            runtime_case = dict(case)
            runtime_case["prompt"] = build_prompt(runtime_case, case_runtime_path)
            runtime_result = evaluate_runtime_case(runtime_case, runtime_template, case_workspace, prompt_path)
            result = {
                "golden_case_id": case["golden_case_id"],
                "case_set": args.case_set,
                "category": case["category"],
                "java_file": case["java_file_relative"],
                "expected_findings": case["expected_findings"],
                **runtime_result,
                "validation_mode": validation_mode,
            }
        else:
            passed, reason = evaluate_static_case(case, rule_sections)
            result = {
                "golden_case_id": case["golden_case_id"],
                "case_set": args.case_set,
                "category": case["category"],
                "java_file": case["java_file_relative"],
                "expected_findings": case["expected_findings"],
                "actual_findings": [],
                "matched_findings": [],
                "missed_findings": [],
                "unexpected_findings": [],
                "rule_id_alignment_issues": [],
                "must_not_violations": [],
                "template_compliance": False,
                "workflow_compliance": False,
                "quality_pass": False,
                "scope_pass": True,
                "format_pass": False,
                "overall_pass": False,
                "precision_estimate": 0.0,
                "recall_estimate": 0.0,
                "command": None,
                "working_directory": None,
                "exit_code": None,
                "stdout": None,
                "stderr": None,
                "passed": passed,
                "validation_mode": validation_mode,
                "reason": reason,
            }
        results.append(result)

    golden_results_path = output_dir / "golden_results.jsonl"
    summary_path = output_dir / "golden_summary.json"
    manifest_path = output_dir / "spec_source_manifest.json"
    readme_path = (skill_root / "skill_validation" / "README_golden.md").resolve()

    gate_a, gate_a_notes = gate_a_status(source_manifest, manifest_notes)
    gate_b, gate_b_notes = gate_b_status(cases, rule_sections)
    gate_c, gate_c_notes = gate_c_status(validation_mode, results)
    gate_d, gate_d_notes = gate_d_status(validation_mode, results)

    passed_cases = sum(1 for result in results if result["passed"])
    failed_cases = len(results) - passed_cases
    quality_passed_cases = sum(1 for result in results if result["quality_pass"])
    scope_passed_cases = sum(1 for result in results if result["scope_pass"])
    format_passed_cases = sum(1 for result in results if result["format_pass"])
    overall_passed_cases = sum(1 for result in results if result["overall_pass"])
    template_failures = [result["golden_case_id"] for result in results if not result["template_compliance"]]
    workflow_failures = [result["golden_case_id"] for result in results if not result["workflow_compliance"]]
    must_not_violations = [
        {
            "golden_case_id": result["golden_case_id"],
            "violations": result["must_not_violations"],
        }
        for result in results
        if result["must_not_violations"]
    ]
    rule_id_alignment_failures = [
        {
            "golden_case_id": result["golden_case_id"],
            "issues": result["rule_id_alignment_issues"],
        }
        for result in results
        if result["rule_id_alignment_issues"]
    ]
    high_risk_missed = [
        {
            "golden_case_id": result["golden_case_id"],
            "missed": missed,
        }
        for result in results
        for missed in result["missed_findings"]
        if missed["severity"] in {"critical", "high"}
    ]
    average_precision = sum(result["precision_estimate"] for result in results) / len(results) if results else 0.0
    average_recall = sum(result["recall_estimate"] for result in results) / len(results) if results else 0.0

    summary: dict[str, Any] = {
        "working_directory": str(skill_root),
        "command": invocation_command,
        "exit_code": 0,
        "case_set": args.case_set,
        "validation_mode": validation_mode,
        "total_golden_cases": len(results),
        "passed_golden_cases": passed_cases,
        "failed_golden_cases": failed_cases,
        "quality_passed_golden_cases": quality_passed_cases,
        "scope_passed_golden_cases": scope_passed_cases,
        "format_passed_golden_cases": format_passed_cases,
        "overall_passed_golden_cases": overall_passed_cases,
        "skipped_golden_cases": 0,
        "average_precision_estimate": round(average_precision, 4),
        "average_recall_estimate": round(average_recall, 4),
        "high_risk_missed_findings": high_risk_missed,
        "must_not_violations": must_not_violations,
        "rule_id_alignment_failures": rule_id_alignment_failures,
        "template_failures": template_failures,
        "workflow_failures": workflow_failures,
        "gate_status": {
            "gate_a_spec_sources": gate_a,
            "gate_b_golden_case_design": gate_b,
            "gate_c_runtime_honesty": gate_c,
            "gate_d_match_quality": gate_d,
            "gate_e_result_honesty": "pending",
        },
        "output_files": {
            "golden_results_relative": relative_to_root(golden_results_path, skill_root),
            "golden_results_absolute": str(golden_results_path),
            "golden_summary_relative": relative_to_root(summary_path, skill_root),
            "golden_summary_absolute": str(summary_path),
            "readme_relative": relative_to_root(readme_path, skill_root),
            "readme_absolute": str(readme_path),
        },
        "notes": manifest_notes + case_notes + runtime_notes + gate_a_notes + gate_b_notes + gate_c_notes + gate_d_notes,
    }

    gate_e, gate_e_notes = gate_e_status(summary, results)
    summary["gate_status"]["gate_e_result_honesty"] = gate_e
    summary["notes"].extend(gate_e_notes)

    write_jsonl(golden_results_path, results)
    write_json(
        manifest_path,
        {
            "skill_root": str(skill_root),
            "sources": source_manifest,
        },
    )
    write_json(summary_path, summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
