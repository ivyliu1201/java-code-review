#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

from run_golden_tests import (
    build_runtime_command,
    build_source_manifest,
    compare_finding,
    detect_must_not_violations,
    detect_runtime_command,
    extract_filenames,
    extract_heading_section,
    gate_a_status,
    gate_c_status,
    gate_d_status,
    gate_e_status,
    is_template_compliant,
    is_workflow_compliant,
    parse_actual_findings,
    parse_rule_sections,
    read_text_with_fallback,
    relative_to_root,
    resolve_skill_root,
    write_json,
    write_jsonl,
)


REQUIRED_SOURCES = [
    "SKILL.md",
    "references/report-templates.md",
    "references/review-workflow.md",
    "references/java-rules.md",
]
RUNTIME_ENV_KEY = "CODEX_RUNTIME_COMMAND"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run diff/PR golden tests for java-code-review skill.")
    parser.add_argument("--skill-root", default=".", help="Skill root directory.")
    parser.add_argument("--output-dir", required=True, help="Diff golden test output directory.")
    parser.add_argument(
        "--validation-mode",
        choices=("auto", "runtime", "static"),
        default="auto",
        help="Validation mode selection.",
    )
    return parser.parse_args()


def build_diff_case_specs() -> list[dict[str, Any]]:
    return [
        {
            "golden_case_id": "security-diff-01",
            "category": "security",
            "source_rules_under_test": ["H-2"],
            "must_not_findings": ["NullPointerException 風險", "交易邊界錯誤"],
            "base_files": {
                "src/main/java/com/example/profile/UserProfileController.java": """package com.example.profile;

public class UserProfileController {
    public UserProfileResponse getProfile(User user) {
        return new UserProfileResponse(
                user.getName(),
                maskMobile(user.getMobile()),
                maskEmail(user.getEmail()));
    }

    private String maskMobile(String mobile) {
        return mobile == null ? null : mobile.substring(0, 3) + "****";
    }

    private String maskEmail(String email) {
        return email == null ? null : "****";
    }
}
""",
                "src/main/java/com/example/legacy/LegacyStatusService.java": """package com.example.legacy;

public class LegacyStatusService {
    public boolean isPaid(Order order) {
        return order.getStatus().equals("PAID");
    }
}
""",
            },
            "changed_files": {
                "src/main/java/com/example/profile/UserProfileController.java": """package com.example.profile;

public class UserProfileController {
    public UserProfileResponse getProfile(User user) {
        return new UserProfileResponse(
                user.getName(),
                user.getMobile(),
                user.getEmail(),
                user.getCardNo());
    }
}
""",
            },
            "expected_findings": [
                {
                    "rule_id": "H-2",
                    "severity": "high",
                    "expected_issue": "Diff 直接回傳完整敏感資料，沒有做最小化與脫敏。",
                    "expected_evidence": "完整手機 Email 卡號 移除脫敏",
                    "expected_recommendation": "不要在 response 直接回傳完整敏感欄位，改為最小化欄位與脫敏後值。",
                    "expected_filename": "userprofilecontroller.java",
                }
            ],
        },
        {
            "golden_case_id": "null-safety-diff-01",
            "category": "null_safety",
            "source_rules_under_test": ["B-1"],
            "must_not_findings": ["敏感資料外洩", "SQL injection"],
            "base_files": {
                "src/main/java/com/example/order/OrderStatusChecker.java": """package com.example.order;

public class OrderStatusChecker {
    public boolean isPaid(Order order) {
        return "PAID".equals(order.getStatus());
    }
}
""",
                "src/main/java/com/example/cache/SessionCacheService.java": """package com.example.cache;

public class SessionCacheService {
    public void save(UserSession session, CacheClient cacheClient) {
        cacheClient.put("session:" + session.getUserId(), session.getAccessToken());
    }
}
""",
            },
            "changed_files": {
                "src/main/java/com/example/order/OrderStatusChecker.java": """package com.example.order;

public class OrderStatusChecker {
    public boolean isPaid(Order order) {
        return order.getStatus().equals("PAID");
    }
}
""",
            },
            "expected_findings": [
                {
                    "rule_id": "B-1",
                    "severity": "medium",
                    "expected_issue": "Diff 對可能為 null 的值主動呼叫 equals，存在 NullPointerException 風險。",
                    "expected_evidence": "order.getStatus().equals(\"PAID\")",
                    "expected_recommendation": "改用常量發起 equals，例如 \"PAID\".equals(order.getStatus())，必要時補 null guard。",
                    "expected_filename": "orderstatuschecker.java",
                }
            ],
        },
        {
            "golden_case_id": "transaction-diff-01",
            "category": "transaction",
            "source_rules_under_test": ["L-1"],
            "must_not_findings": ["命名規則違反", "常數規則違反"],
            "base_files": {
                "src/main/java/com/example/checkout/CheckoutService.java": """package com.example.checkout;

public class CheckoutService {
    private final OrderRepository orderRepository;
    private final PaymentOrchestrator paymentOrchestrator;

    public CheckoutService(OrderRepository orderRepository, PaymentOrchestrator paymentOrchestrator) {
        this.orderRepository = orderRepository;
        this.paymentOrchestrator = paymentOrchestrator;
    }

    public void completeCheckout(CheckoutRequest request) {
        orderRepository.save(request.toOrder());
        paymentOrchestrator.requestCharge(request.getOrderId(), request.getAmount());
    }
}
""",
                "src/main/java/com/example/legacy/LegacyProfileService.java": """package com.example.legacy;

public class LegacyProfileService {
    public UserProfileResponse build(User user) {
        return new UserProfileResponse(user.getName(), user.getIdNo());
    }
}
""",
            },
            "changed_files": {
                "src/main/java/com/example/checkout/CheckoutService.java": """package com.example.checkout;

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
            },
            "expected_findings": [
                {
                    "rule_id": "L-1",
                    "severity": "high",
                    "expected_issue": "Diff 在 @Transactional 交易內直接呼叫外部支付系統，可能破壞交易一致性。",
                    "expected_evidence": "@Transactional paymentClient.charge",
                    "expected_recommendation": "把外部呼叫移出本地交易邊界，或改用可補償的非同步 / outbox 設計。",
                    "expected_filename": "checkoutservice.java",
                }
            ],
        },
        {
            "golden_case_id": "performance-diff-01",
            "category": "performance",
            "source_rules_under_test": ["F-3"],
            "must_not_findings": ["交易邊界錯誤", "命名規則違反"],
            "base_files": {
                "src/main/java/com/example/query/OrderQueryService.java": """package com.example.query;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OrderQueryService {
    private static final Logger log = LoggerFactory.getLogger(OrderQueryService.class);
    private final ObjectMapper objectMapper = new ObjectMapper();

    public void query(List<OrderResponse> responses) throws JsonProcessingException {
        for (OrderResponse response : responses) {
            log.debug("response={}", response.getOrderId());
        }
    }
}
""",
                "src/main/java/com/example/legacy/LegacyCheckoutService.java": """package com.example.legacy;

public class LegacyCheckoutService {
    public void complete(CheckoutRequest request, PaymentClient paymentClient) {
        paymentClient.charge(request.getPaymentToken(), request.getAmount());
    }
}
""",
            },
            "changed_files": {
                "src/main/java/com/example/query/OrderQueryService.java": """package com.example.query;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OrderQueryService {
    private static final Logger log = LoggerFactory.getLogger(OrderQueryService.class);
    private final ObjectMapper objectMapper = new ObjectMapper();

    public void query(List<OrderResponse> responses) throws JsonProcessingException {
        for (OrderResponse response : responses) {
            log.debug("response=" + objectMapper.writeValueAsString(response));
        }
    }
}
""",
            },
            "expected_findings": [
                {
                    "rule_id": "F-3",
                    "severity": "medium",
                    "expected_issue": "Diff 在迴圈中使用無條件字串拼接與序列化日誌，會造成不必要的效能成本。",
                    "expected_evidence": "for log.debug objectMapper.writeValueAsString(response)",
                    "expected_recommendation": "改用參數化日誌，若序列化成本高則加 log level guard，避免在迴圈中每次都做昂貴字串組裝。",
                    "expected_filename": "orderqueryservice.java",
                }
            ],
        },
        {
            "golden_case_id": "maintainability-diff-01",
            "category": "maintainability",
            "source_rules_under_test": ["L-3"],
            "must_not_findings": ["NullPointerException 風險", "交易邊界錯誤"],
            "base_files": {
                "src/main/java/com/example/user/UserController.java": """package com.example.user;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class UserController {
    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @PostMapping("/users")
    public UserResponse create(@RequestBody CreateUserRequest request) {
        return userService.create(request);
    }
}
""",
                "src/main/java/com/example/legacy/LegacyAuditService.java": """package com.example.legacy;

public class LegacyAuditService {
    public void record(String action, User user) {
        System.out.println(user.getPassword());
    }
}
""",
            },
            "changed_files": {
                "src/main/java/com/example/user/UserController.java": """package com.example.user;

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
            },
            "expected_findings": [
                {
                    "rule_id": "L-3",
                    "severity": "high",
                    "expected_issue": "Diff 直接使用 Entity 作為 request 與 response，會讓 API 邊界與資料模型耦合。",
                    "expected_evidence": "@RequestBody UserEntity return userRepository.save(user)",
                    "expected_recommendation": "改用明確的 CreateUserRequest 與 UserResponse，避免直接接收或回傳 Entity。",
                    "expected_filename": "usercontroller.java",
                }
            ],
        },
    ]


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def on_rm_error(func: Any, path: str, _exc_info: Any) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def prepare_git_case_repo(case_workspace: Path, case: dict[str, Any]) -> tuple[list[str], list[str], str]:
    if case_workspace.exists():
        shutil.rmtree(case_workspace, onexc=on_rm_error)
    case_workspace.mkdir(parents=True, exist_ok=True)

    for relative_path, content in case["base_files"].items():
        target = case_workspace / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    readme_path = case_workspace / "README.md"
    readme_path.write_text("# diff harness repo\n", encoding="utf-8")

    init_commands = [
        ["git", "init"],
        ["git", "config", "user.name", "Codex Diff Harness"],
        ["git", "config", "user.email", "codex-diff-harness@example.com"],
        ["git", "add", "README.md"],
        ["git", "commit", "-m", "repo init"],
        ["git", "add", "."],
        ["git", "commit", "-m", "base snapshot"],
    ]
    for command in init_commands:
        completed = run_command(command, case_workspace)
        if completed.returncode != 0:
            raise RuntimeError(
                f"git repo 初始化失敗: {' '.join(command)}\nstdout={completed.stdout}\nstderr={completed.stderr}"
            )

    for relative_path, content in case["changed_files"].items():
        target = case_workspace / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    diff_completed = run_command(["git", "diff", "--", "*.java"], case_workspace)
    if diff_completed.returncode not in (0, 1):
        raise RuntimeError(f"git diff 失敗: {diff_completed.stderr}")

    changed_files = sorted(Path(path).name for path in case["changed_files"].keys() if path.endswith(".java"))
    unchanged_files = sorted(
        Path(path).name
        for path in case["base_files"].keys()
        if path.endswith(".java") and path not in case["changed_files"]
    )
    return changed_files, unchanged_files, diff_completed.stdout


def build_prompt(case: dict[str, Any], changed_files: list[str], diff_text: str) -> str:
    rule_excerpt = case.get("rule_excerpt", "").strip()
    changed_files_text = ", ".join(changed_files)
    rule_ids_text = ", ".join(case.get("source_rules_under_test", []))
    return (
        "請對這個 Java diff 做正式 code review。\n"
        "只審查目前 diff 中有變更的 Java 檔案，不得提到未變更檔案名稱。\n"
        f"本次 diff 中有變更的 Java 檔案只有：{changed_files_text}\n"
        f"本 case 主要檢查的本地 rule id：{rule_ids_text}。若列出相關 finding，請盡量在 `規則` 欄標出精確 rule id。\n\n"
        "本地規則摘要：\n"
        f"{rule_excerpt}\n\n"
        "Git diff:\n"
        "```diff\n"
        f"{diff_text.strip()}\n"
        "```\n\n"
        "輸出偏好：\n"
        "- 使用繁體中文。\n"
        "- 正式報告優先使用中文表格呈現 `問題清單`。\n"
        "- 若有問題，請附檔案與行號。\n"
        "- 盡量交代審查範圍、開放問題與剩餘風險。\n"
    )


def generate_cases(
    skill_root: Path,
    diff_cases_dir: Path,
    rule_sections: dict[str, str],
    source_texts: dict[str, str],
) -> tuple[list[dict[str, Any]], list[str]]:
    notes: list[str] = []
    cases = build_diff_case_specs()
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
        case["rule_excerpt"] = "\n\n".join(
            rule_sections[rule_id] for rule_id in case["source_rules_under_test"] if rule_id in rule_sections
        )
        case["template_excerpt"] = compact_template
        case["workflow_excerpt"] = compact_workflow
        case["case_root_absolute"] = str((diff_cases_dir / case["golden_case_id"]).resolve())
    return cases, notes


def detect_scope_violations(actual_findings: list[dict[str, Any]], changed_files: list[str]) -> list[dict[str, Any]]:
    changed_files_lower = {name.lower() for name in changed_files}
    violations: list[dict[str, Any]] = []
    for actual in actual_findings:
        referenced = extract_filenames(" ".join(actual.get("raw_lines", [])))
        off_scope = sorted(name for name in referenced if name not in changed_files_lower)
        if off_scope:
            violations.append(
                {
                    "title": actual.get("title", ""),
                    "off_scope_files": off_scope,
                }
            )
    return violations


def detect_unchanged_file_mentions(stdout: str, unchanged_files: list[str]) -> list[str]:
    normalized = stdout.lower()
    return [name for name in unchanged_files if name.lower() in normalized]


def evaluate_static_case(case: dict[str, Any], rule_sections: dict[str, str]) -> tuple[bool, str]:
    if not case["expected_findings"]:
        return False, "case 缺少 expected_findings。"
    if not case["must_not_findings"]:
        return False, "case 缺少 must_not_findings。"
    if not case["changed_files"]:
        return False, "case 缺少 changed_files。"
    for expected in case["expected_findings"]:
        required_keys = (
            "rule_id",
            "severity",
            "expected_issue",
            "expected_evidence",
            "expected_recommendation",
            "expected_filename",
        )
        if any(not expected.get(key) for key in required_keys):
            return False, f"expected finding 缺少欄位：{expected}"
        if expected["rule_id"] not in rule_sections:
            return False, f"expected finding 的 rule_id 無法對應 java-rules.md：{expected['rule_id']}"
    return True, "static mode 僅驗證 diff case 結構、rule 對應與比對邏輯存在，未實際驗證 diff review 準確度。"


def evaluate_runtime_case(
    case: dict[str, Any],
    runtime_template: list[str],
    case_workspace: Path,
    prompt_path: Path,
    changed_files: list[str],
    unchanged_files: list[str],
) -> dict[str, Any]:
    command_list = build_runtime_command(runtime_template, case["prompt"], case_workspace, prompt_path)
    last_message_path = prompt_path.with_name(f"{case['golden_case_id']}_last_message.txt")
    command_name = Path(command_list[0]).name.lower()
    if command_name.startswith("codex") and "--output-last-message" not in command_list and "-o" not in command_list:
        command_list.extend(["--output-last-message", str(last_message_path), "--color", "never"])

    timeout_seconds = 420
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
        stdout_text = completed.stdout
        if last_message_path.exists():
            stdout_text = read_text_with_fallback(last_message_path)
        exit_code = completed.returncode
        stderr_text = completed.stderr
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout_text = read_text_with_fallback(last_message_path) if last_message_path.exists() else (exc.stdout or "")
        stderr_text = (exc.stderr or "") + f"\nTimeoutExpired after {timeout_seconds} seconds."
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
    scope_violations = detect_scope_violations(actual_findings, changed_files)
    unchanged_file_mentions = detect_unchanged_file_mentions(stdout_text, unchanged_files)
    precision = 0.0 if not actual_findings else len(matched_findings) / len(actual_findings)
    recall = 0.0 if not case["expected_findings"] else len(matched_findings) / len(case["expected_findings"])
    quality_pass = (
        exit_code == 0
        and not missed_findings
        and not must_not_violations
    )
    scope_pass = not scope_violations and not unchanged_file_mentions
    format_pass = template_compliance and workflow_compliance
    overall_pass = quality_pass and scope_pass and format_pass

    if timed_out:
        reason = f"runtime mode 執行逾時，case 已記錄為失敗；timeout={timeout_seconds}s。"
    elif not actual_findings:
        reason = "runtime mode 已執行，但沒有解析到 actual findings；precision 不代表真實準確度。"
    elif overall_pass:
        reason = "runtime mode 比對通過。"
    elif quality_pass and scope_pass and not format_pass:
        reason = "runtime mode diff finding 品質與 scope 通過，但輸出格式或 workflow 訊號不符合契約。"
    elif quality_pass and not scope_pass and format_pass:
        reason = "runtime mode finding 品質符合，但 diff scope 控制未通過。"
    elif not quality_pass and scope_pass and format_pass:
        reason = "runtime mode scope 與格式符合契約，但 diff finding 品質未通過。"
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
        "scope_violations": scope_violations,
        "unchanged_file_mentions": unchanged_file_mentions,
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


def gate_b_status(cases: list[dict[str, Any]], rule_sections: dict[str, str]) -> tuple[str, list[str]]:
    issues: list[str] = []
    categories = {case["category"] for case in cases}
    required_categories = {"security", "null_safety", "performance", "maintainability", "transaction"}
    if len(cases) < 5:
        issues.append("diff golden cases 少於 5 個。")
    if not required_categories.issubset(categories):
        issues.append("diff golden cases 缺少必要類別。")

    for case in cases:
        if not case["base_files"]:
            issues.append(f"{case['golden_case_id']} 沒有 base_files。")
        if not case["changed_files"]:
            issues.append(f"{case['golden_case_id']} 沒有 changed_files。")
        if not case["expected_findings"]:
            issues.append(f"{case['golden_case_id']} 沒有 expected finding。")
        if not case["must_not_findings"]:
            issues.append(f"{case['golden_case_id']} 沒有 must_not finding。")
        for expected in case["expected_findings"]:
            for key in (
                "expected_issue",
                "expected_evidence",
                "severity",
                "expected_recommendation",
                "expected_filename",
            ):
                if not expected.get(key):
                    issues.append(f"{case['golden_case_id']} 的 expected finding 缺少 {key}。")
            if expected["rule_id"] not in rule_sections:
                issues.append(f"{case['golden_case_id']} 的 rule_id {expected['rule_id']} 無法對應 java-rules.md。")
    return ("fail" if issues else "pass"), issues


def run(args: argparse.Namespace) -> int:
    skill_root = resolve_skill_root(Path(args.skill_root))
    output_dir = (skill_root / args.output_dir).resolve() if not Path(args.output_dir).is_absolute() else Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    diff_cases_dir = (skill_root / "skill_validation" / "diff_cases").resolve()
    diff_cases_dir.mkdir(parents=True, exist_ok=True)
    case_workspaces_dir = (output_dir / "case_workspaces").resolve()
    case_workspaces_dir.mkdir(parents=True, exist_ok=True)

    invocation_command = " ".join(shlex.quote(part) for part in [sys.executable, *sys.argv])

    source_manifest, source_texts, manifest_notes = build_source_manifest(skill_root)
    java_rules_text = source_texts.get("references/java-rules.md", "")
    rule_sections = parse_rule_sections(java_rules_text) if java_rules_text else {}
    cases, case_notes = generate_cases(skill_root, diff_cases_dir, rule_sections, source_texts)

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
        changed_files, unchanged_files, diff_text = prepare_git_case_repo(case_workspace, case)
        prompt_path = case_workspace / "runtime_prompt.txt"
        if validation_mode == "runtime_validation" and runtime_template is not None:
            runtime_case = dict(case)
            runtime_case["prompt"] = build_prompt(runtime_case, changed_files, diff_text)
            runtime_result = evaluate_runtime_case(
                runtime_case,
                runtime_template,
                case_workspace,
                prompt_path,
                changed_files,
                unchanged_files,
            )
            result = {
                "golden_case_id": case["golden_case_id"],
                "scenario": "diff_pr",
                "category": case["category"],
                "changed_files": changed_files,
                "unchanged_files": unchanged_files,
                "expected_findings": case["expected_findings"],
                **runtime_result,
                "validation_mode": validation_mode,
            }
        else:
            passed, reason = evaluate_static_case(case, rule_sections)
            result = {
                "golden_case_id": case["golden_case_id"],
                "scenario": "diff_pr",
                "category": case["category"],
                "changed_files": changed_files,
                "unchanged_files": unchanged_files,
                "expected_findings": case["expected_findings"],
                "actual_findings": [],
                "matched_findings": [],
                "missed_findings": [],
                "unexpected_findings": [],
                "rule_id_alignment_issues": [],
                "must_not_violations": [],
                "template_compliance": False,
                "workflow_compliance": False,
                "scope_violations": [],
                "unchanged_file_mentions": [],
                "quality_pass": False,
                "scope_pass": False,
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
    readme_path = (skill_root / "skill_validation" / "README_diff_golden.md").resolve()

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
    scope_failures = [
        {
            "golden_case_id": result["golden_case_id"],
            "scope_violations": result["scope_violations"],
            "unchanged_file_mentions": result["unchanged_file_mentions"],
        }
        for result in results
        if result["scope_violations"] or result["unchanged_file_mentions"]
    ]
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
        "scenario": "diff_pr",
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
        "scope_failures": scope_failures,
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
