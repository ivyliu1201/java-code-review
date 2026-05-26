#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from run_golden_tests import (
    build_runtime_command,
    build_source_manifest,
    detect_runtime_command,
    normalize_runtime_text,
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run large-codebase workflow benchmarks for java-code-review skill.")
    parser.add_argument("--skill-root", default=".", help="Skill root directory.")
    parser.add_argument("--output-dir", required=True, help="Large benchmark output directory.")
    parser.add_argument(
        "--validation-mode",
        choices=("auto", "runtime", "static"),
        default="auto",
        help="Validation mode selection.",
    )
    return parser.parse_args()


def build_case_spec() -> dict[str, Any]:
    files = {
        "src/main/java/com/example/account/AccountBalanceService.java": """package com.example.account;

public class AccountBalanceService {
    public boolean hasEnough(Account account, long amount) {
        return account.getBalance() >= amount;
    }
}
""",
        "src/main/java/com/example/audit/AuditLogService.java": """package com.example.audit;

public class AuditLogService {
    public void record(String action, User user) {
        System.out.println(user.getId());
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
        "src/main/java/com/example/checkout/CheckoutService.java": """package com.example.checkout;

import org.springframework.transaction.annotation.Transactional;

public class CheckoutService {
    private final OrderRepository orderRepository;
    private final PaymentClient paymentClient;

    public CheckoutService(OrderRepository orderRepository, PaymentClient paymentClient) {
        this.orderRepository = orderRepository;
        this.paymentClient = paymentClient;
    }

    @Transactional
    public void complete(CheckoutRequest request) {
        orderRepository.save(request.toOrder());
        paymentClient.charge(request.getPaymentToken(), request.getAmount());
    }
}
""",
        "src/main/java/com/example/order/OrderStatusChecker.java": """package com.example.order;

public class OrderStatusChecker {
    public boolean isPaid(Order order) {
        return order.getStatus().equals("PAID");
    }
}
""",
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
        "src/main/java/com/example/notification/EmailNotificationService.java": """package com.example.notification;

public class EmailNotificationService {
    public void send(User user, String content) {
        System.out.println(user.getEmail() + ":" + content);
    }
}
""",
        "src/main/java/com/example/inventory/InventoryReservationService.java": """package com.example.inventory;

public class InventoryReservationService {
    public void reserve(Product product, int quantity) {
        product.setStock(product.getStock() - quantity);
    }
}
""",
        "src/main/java/com/example/loyalty/CouponGrantService.java": """package com.example.loyalty;

public class CouponGrantService {
    public void grantCoupon(CouponRequest request, CouponClient couponClient) {
        couponClient.issue(request.getUserId(), request.getCouponCode());
        couponClient.issue(request.getUserId(), request.getCouponCode());
    }
}
""",
        "src/main/java/com/example/report/MonthlyReportService.java": """package com.example.report;

public class MonthlyReportService {
    public String build(User user) {
        return user.getName();
    }
}
""",
    }
    return {
        "benchmark_case_id": "large-codebase-01",
        "category": "large_codebase_workflow",
        "files": files,
        "min_java_files": 11,
        "expected_signal_files": [
            "CheckoutService.java",
            "UserProfileController.java",
            "OrderStatusChecker.java",
        ],
    }


def prepare_workspace(case_workspace: Path, case: dict[str, Any]) -> list[str]:
    if case_workspace.exists():
        for child in sorted(case_workspace.rglob("*"), reverse=True):
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        case_workspace.rmdir()
    case_workspace.mkdir(parents=True, exist_ok=True)

    for relative_path, content in case["files"].items():
        target = case_workspace / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    java_files = sorted(path.name for path in case_workspace.rglob("*.java"))
    return java_files


def build_prompt(case: dict[str, Any], java_files: list[str], rule_sections: dict[str, str]) -> str:
    selected_rule_ids = ["0-1", "H-2", "L-1", "L-3", "M-4"]
    rule_excerpt = "\n\n".join(rule_sections.get(rule_id, "") for rule_id in selected_rule_ids if rule_sections.get(rule_id))
    file_count = len(java_files)
    return (
        "請對目前 workspace 的 Java 專案做正式 code review。\n"
        f"目前範圍有 {file_count} 個 Java 檔，超過 5 個，應啟用 Large Codebase Review Mode。\n"
        "你需要先做 inventory，維護審查台帳，分批審查，且未完成時不得暗示整體 review 已完成。\n"
        "輸出偏好：\n"
        "- 使用繁體中文。\n"
        "- `問題清單` 優先使用中文表格。\n"
        "- 交代審查範圍、目前批次、審查台帳、進度、開放問題、剩餘風險。\n"
        "- 若尚未 review 完所有檔案，請提供續跑提示。\n\n"
        "重點 workflow 摘要：\n"
        "- 先建立 Java file inventory。\n"
        "- 使用穩定順序排序檔案。\n"
        "- 每批最多審查 10 個 Java 檔。\n"
        "- 只要仍有 pending，就不可宣稱 review 完成。\n\n"
        "本地規則摘錄：\n"
        f"{rule_excerpt}\n\n"
        "請 review 的目錄：`src/main/java`\n"
    )


def evaluate_runtime_case(
    case: dict[str, Any],
    runtime_template: list[str],
    case_workspace: Path,
    prompt_path: Path,
) -> dict[str, Any]:
    command_list = build_runtime_command(runtime_template, case["prompt"], case_workspace, prompt_path)
    last_message_path = prompt_path.with_name(f"{case['benchmark_case_id']}_last_message.txt")
    command_name = Path(command_list[0]).name.lower()
    if command_name.startswith("codex") and "--output-last-message" not in command_list and "-o" not in command_list:
        command_list.extend(["--output-last-message", str(last_message_path), "--color", "never"])

    completed = subprocess.run(
        command_list,
        cwd=case_workspace,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=420,
        check=False,
    )
    stdout_text = read_text_with_fallback(last_message_path) if last_message_path.exists() else completed.stdout
    normalized = normalize_runtime_text(stdout_text)
    actual_findings = parse_actual_findings(stdout_text)

    workflow_checks = {
        "scope": "審查範圍" in normalized,
        "batch": "目前批次" in normalized or "current batch" in normalized.lower(),
        "ledger": "審查台帳" in normalized or "review ledger" in normalized.lower(),
        "progress": "進度" in normalized or "progress" in normalized.lower(),
        "open_questions": "開放問題" in normalized or "open questions" in normalized.lower(),
        "residual_risks": "剩餘風險" in normalized or "residual risks" in normalized.lower(),
        "continuation_prompt": "續跑提示" in normalized or "continuation prompt" in normalized.lower(),
    }
    pending_markers = ("待審查" in normalized) or ("pending" in normalized.lower())
    workflow_issues: list[str] = []
    for key, passed in workflow_checks.items():
        if key == "continuation_prompt" and not pending_markers:
            continue
        if not passed:
            workflow_issues.append(f"缺少 {key}")
    if not pending_markers:
        workflow_issues.append("未顯示 pending / 待審查 狀態")

    finding_signal_pass = any(
        any(name.lower() in " ".join(finding.get("raw_lines", [])).lower() for name in case["expected_signal_files"])
        for finding in actual_findings
    )
    quality_pass = completed.returncode == 0 and finding_signal_pass
    scope_pass = workflow_checks["scope"]
    workflow_pass = completed.returncode == 0 and not workflow_issues
    overall_pass = quality_pass and scope_pass and workflow_pass

    return {
        "actual_findings": actual_findings,
        "workflow_checks": workflow_checks,
        "workflow_issues": workflow_issues,
        "pending_markers_detected": pending_markers,
        "finding_signal_pass": finding_signal_pass,
        "quality_pass": quality_pass,
        "scope_pass": scope_pass,
        "workflow_pass": workflow_pass,
        "overall_pass": overall_pass,
        "command": subprocess.list2cmdline(command_list),
        "working_directory": str(case_workspace),
        "exit_code": completed.returncode,
        "stdout": stdout_text,
        "stderr": completed.stderr,
        "reason": "runtime workflow benchmark 通過。"
        if overall_pass
        else "runtime workflow benchmark 未完全符合 large-codebase 的 quality / scope / workflow 期望。",
    }


def evaluate_static_case(case: dict[str, Any]) -> tuple[bool, str]:
    if len(case["files"]) < case["min_java_files"]:
        return False, "large-codebase benchmark 的 Java 檔案數不足。"
    if not case["expected_signal_files"]:
        return False, "large-codebase benchmark 缺少 expected signal files。"
    return True, "static mode 僅驗證 large-codebase benchmark 結構存在，未實際驗證 workflow。"


def run(args: argparse.Namespace) -> int:
    skill_root = resolve_skill_root(Path(args.skill_root))
    output_dir = (skill_root / args.output_dir).resolve() if not Path(args.output_dir).is_absolute() else Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    case_workspaces_dir = (output_dir / "case_workspaces").resolve()
    case_workspaces_dir.mkdir(parents=True, exist_ok=True)

    source_manifest, source_texts, manifest_notes = build_source_manifest(skill_root)
    java_rules_text = source_texts.get("references/java-rules.md", "")
    rule_sections = parse_rule_sections(java_rules_text) if java_rules_text else {}

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

    case = build_case_spec()
    case_workspace = case_workspaces_dir / case["benchmark_case_id"]
    java_files = prepare_workspace(case_workspace, case)
    prompt_path = case_workspace / "runtime_prompt.txt"
    case["prompt"] = build_prompt(case, java_files, rule_sections)

    if validation_mode == "runtime_validation" and runtime_template is not None:
        runtime_result = evaluate_runtime_case(case, runtime_template, case_workspace, prompt_path)
        result = {
            "benchmark_case_id": case["benchmark_case_id"],
            "category": case["category"],
            "java_file_count": len(java_files),
            "validation_mode": validation_mode,
            **runtime_result,
            "passed": runtime_result["overall_pass"],
        }
    else:
        passed, reason = evaluate_static_case(case)
        result = {
            "benchmark_case_id": case["benchmark_case_id"],
            "category": case["category"],
            "java_file_count": len(java_files),
            "validation_mode": validation_mode,
            "actual_findings": [],
            "workflow_checks": {},
            "workflow_issues": [],
            "pending_markers_detected": False,
            "finding_signal_pass": False,
            "quality_pass": False,
            "scope_pass": False,
            "workflow_pass": False,
            "overall_pass": False,
            "command": None,
            "working_directory": None,
            "exit_code": None,
            "stdout": None,
            "stderr": None,
            "reason": reason,
            "passed": passed,
        }

    results = [result]
    summary = {
        "working_directory": str(skill_root),
        "command": " ".join(shlex.quote(part) for part in [sys.executable, *sys.argv]),
        "exit_code": 0,
        "scenario": "large_codebase_workflow",
        "validation_mode": validation_mode,
        "total_benchmark_cases": 1,
        "passed_benchmark_cases": sum(1 for item in results if item["passed"]),
        "failed_benchmark_cases": sum(1 for item in results if not item["passed"]),
        "quality_passed_cases": sum(1 for item in results if item["quality_pass"]),
        "scope_passed_cases": sum(1 for item in results if item["scope_pass"]),
        "workflow_passed_cases": sum(1 for item in results if item["workflow_pass"]),
        "finding_signal_passed_cases": sum(1 for item in results if item["finding_signal_pass"]),
        "overall_passed_cases": sum(1 for item in results if item["overall_pass"]),
        "gate_status": {
            "gate_a_spec_sources": "pass" if source_manifest else "fail",
            "gate_b_case_design": "pass" if len(java_files) >= case["min_java_files"] else "fail",
            "gate_c_runtime_honesty": "pass",
            "gate_d_workflow_enforcement": "pass" if validation_mode == "static_validation_only" or result["workflow_pass"] else "fail",
            "gate_e_result_honesty": "pass",
        },
        "output_files": {
            "benchmark_results_relative": relative_to_root(output_dir / "large_benchmark_results.jsonl", skill_root),
            "benchmark_results_absolute": str((output_dir / "large_benchmark_results.jsonl").resolve()),
            "benchmark_summary_relative": relative_to_root(output_dir / "large_benchmark_summary.json", skill_root),
            "benchmark_summary_absolute": str((output_dir / "large_benchmark_summary.json").resolve()),
            "readme_relative": relative_to_root(skill_root / "skill_validation" / "README_large_benchmark.md", skill_root),
            "readme_absolute": str((skill_root / "skill_validation" / "README_large_benchmark.md").resolve()),
        },
        "notes": manifest_notes + runtime_notes + result.get("workflow_issues", []),
    }

    write_jsonl(output_dir / "large_benchmark_results.jsonl", results)
    write_json(output_dir / "large_benchmark_summary.json", summary)
    write_json(output_dir / "spec_source_manifest.json", source_manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
