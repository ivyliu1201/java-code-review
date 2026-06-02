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
    annotate_cases_with_catalog,
    apply_catalog_fixtures,
    build_benchmark_case_index,
    build_runtime_command,
    build_source_manifest,
    compare_finding,
    detect_must_not_violations,
    detect_runtime_command,
    execute_runtime_command,
    extract_filenames,
    extract_heading_section,
    extract_rule_ids,
    gate_a_status,
    gate_c_status,
    gate_d_status,
    gate_e_status,
    get_benchmark_layer,
    is_template_compliant,
    is_workflow_compliant,
    load_benchmark_catalog,
    parse_actual_findings,
    parse_rule_sections,
    read_text_with_fallback,
    relative_to_root,
    resolve_skill_root,
    summarize_catalog_alignment,
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
DIFF_CATALOG_CASE_MAP = {
    "security-diff-01": ["diff-security-scope-01"],
    "null-safety-diff-01": ["diff-null-safety-01"],
    "transaction-diff-01": ["diff-transaction-01"],
    "performance-diff-01": ["diff-performance-logging-01"],
    "maintainability-diff-01": ["diff-maintainability-01"],
    "cache-scope-diff-01": ["diff-cache-scope-01"],
    "test-only-change-diff-01": ["diff-test-only-change-01"],
    "multi-file-order-diff-01": ["diff-multi-file-order-01"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run diff/PR golden tests for java-code-review skill.")
    parser.add_argument("--skill-root", default=".", help="Skill root directory.")
    parser.add_argument("--output-dir", required=True, help="Diff golden test output directory.")
    parser.add_argument(
        "--case-id",
        action="append",
        default=[],
        help="Only run the specified golden_case_id. Repeat this flag to run multiple cases.",
    )
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
        {
            "golden_case_id": "cache-scope-diff-01",
            "category": "security",
            "source_rules_under_test": ["M-4"],
            "must_not_findings": ["交易邊界錯誤", "NullPointerException 風險"],
            "base_files": {
                "src/main/java/com/example/cache/SessionCacheService.java": """package com.example.cache;

public class SessionCacheService {
    public void save(UserSession session, CacheClient cacheClient) {
        cacheClient.put(
                "session:" + session.getUserId(),
                new SessionSnapshot(session.getUserId(), maskEmail(session.getEmail())));
    }

    private String maskEmail(String email) {
        return email == null ? null : "****";
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
                "src/main/java/com/example/cache/SessionCacheService.java": """package com.example.cache;

public class SessionCacheService {
    public void save(UserSession session, CacheClient cacheClient) {
        cacheClient.put(
                "session:" + session.getUserId(),
                new SessionSnapshot(
                        session.getUserId(),
                        session.getEmail(),
                        session.getAccessToken()));
    }
}
""",
            },
            "expected_findings": [
                {
                    "rule_id": "M-4",
                    "severity": "high",
                    "expected_issue": "Diff 在 cache value 中直接放入完整 email 與 access token，缺少敏感資料最小化與保護。",
                    "expected_evidence": "SessionSnapshot session.getEmail session.getAccessToken",
                    "expected_recommendation": "不要把完整敏感欄位與 token 直接放進 cache，改存必要且脫敏後的資料，並保留明確 TTL/清除策略。",
                    "expected_filename": "sessioncacheservice.java",
                }
            ],
        },
        {
            "golden_case_id": "test-only-change-diff-01",
            "category": "scope",
            "source_rules_under_test": ["K-1", "K-2"],
            "must_not_findings": ["缺少對應測試", "happy path"],
            "allowed_unchanged_file_mentions": ["RefundService.java"],
            "allowed_context_files_in_findings": ["RefundService.java"],
            "base_files": {
                "src/main/java/com/example/refund/RefundService.java": """package com.example.refund;

import java.math.BigDecimal;

public class RefundService {
    public RefundDecision evaluate(RefundRequest request, BigDecimal refundableAmount) {
        if (request.getRefundAmount().compareTo(refundableAmount) > 0) {
            throw new IllegalStateException("amount exceeds refundable amount");
        }
        if (request.getRefundAmount().signum() == 0) {
            return RefundDecision.rejected("ZERO_AMOUNT");
        }
        return RefundDecision.approved();
    }
}
""",
                "src/test/java/com/example/refund/RefundServiceTest.java": """package com.example.refund;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.math.BigDecimal;
import org.junit.jupiter.api.Test;

class RefundServiceTest {
    private final RefundService refundService = new RefundService();

    @Test
    void shouldRejectZeroAmount() {
        RefundDecision decision = refundService.evaluate(
                new RefundRequest(new BigDecimal("0.00")),
                new BigDecimal("100.00"));

        assertEquals("ZERO_AMOUNT", decision.getReason());
    }
}
""",
            },
            "changed_files": {
                "src/test/java/com/example/refund/RefundServiceTest.java": """package com.example.refund;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.math.BigDecimal;
import org.junit.jupiter.api.Test;

class RefundServiceTest {
    private final RefundService refundService = new RefundService();

    @Test
    void shouldRejectZeroAmount() {
        RefundDecision decision = refundService.evaluate(
                new RefundRequest(new BigDecimal("0.00")),
                new BigDecimal("100.00"));

        assertEquals("ZERO_AMOUNT", decision.getReason());
    }

    @Test
    void shouldThrowWhenRefundAmountExceedsRefundableAmount() {
        assertThrows(
                IllegalStateException.class,
                () -> refundService.evaluate(
                        new RefundRequest(new BigDecimal("120.00")),
                        new BigDecimal("100.00")));
    }
}
""",
            },
            "expected_findings": [
                {
                    "rule_id": "K-2",
                    "severity": "medium",
                    "expected_issue": "本次新增測試仍缺少可退額等值邊界案例，測試覆蓋不足以保護退款上限規則。",
                    "expected_evidence": "assertThrows 120.00 100.00 compareTo(refundableAmount) > 0",
                    "expected_recommendation": "補等於可退額的通過案例，並確認退款上限邊界語意有被測試保護。",
                    "expected_filename": "refundservicetest.java",
                }
            ],
        },
        {
            "golden_case_id": "multi-file-order-diff-01",
            "category": "transaction",
            "source_rules_under_test": ["J-16"],
            "must_not_findings": ["NullPointerException 風險", "命名規則違反"],
            "base_files": {
                "src/main/java/com/example/order/OrderApplicationService.java": """package com.example.order;

import java.util.List;
import org.springframework.transaction.annotation.Transactional;

public class OrderApplicationService {
    private final OrderRepository orderRepository;
    private final OrderItemService orderItemService;
    private final OrderSummaryRepository orderSummaryRepository;

    public OrderApplicationService(
            OrderRepository orderRepository,
            OrderItemService orderItemService,
            OrderSummaryRepository orderSummaryRepository) {
        this.orderRepository = orderRepository;
        this.orderItemService = orderItemService;
        this.orderSummaryRepository = orderSummaryRepository;
    }

    @Transactional
    public void createOrder(CreateOrderRequest request) {
        Order order = Order.from(request);
        orderRepository.save(order);
        orderItemService.saveItems(order.getId(), request.getItems());
        orderSummaryRepository.save(OrderSummary.created(order.getId(), request.getItems().size()));
    }
}
""",
                "src/main/java/com/example/order/OrderItemService.java": """package com.example.order;

import java.util.List;

public class OrderItemService {
    private final OrderItemRepository orderItemRepository;

    public OrderItemService(OrderItemRepository orderItemRepository) {
        this.orderItemRepository = orderItemRepository;
    }

    public void saveItems(Long orderId, List<OrderItemRequest> items) {
        orderItemRepository.saveAll(OrderItem.from(orderId, items));
    }
}
""",
            },
            "changed_files": {
                "src/main/java/com/example/order/OrderApplicationService.java": """package com.example.order;

public class OrderApplicationService {
    private final OrderRepository orderRepository;
    private final OrderItemService orderItemService;

    public OrderApplicationService(
            OrderRepository orderRepository,
            OrderItemService orderItemService) {
        this.orderRepository = orderRepository;
        this.orderItemService = orderItemService;
    }

    public void createOrder(CreateOrderRequest request) {
        Order order = Order.from(request);
        orderRepository.save(order);
        orderItemService.saveItemsAndSummary(order.getId(), request.getItems());
    }
}
""",
                "src/main/java/com/example/order/OrderItemService.java": """package com.example.order;

import java.util.List;

public class OrderItemService {
    private final OrderItemRepository orderItemRepository;
    private final OrderSummaryRepository orderSummaryRepository;

    public OrderItemService(
            OrderItemRepository orderItemRepository,
            OrderSummaryRepository orderSummaryRepository) {
        this.orderItemRepository = orderItemRepository;
        this.orderSummaryRepository = orderSummaryRepository;
    }

    public void saveItemsAndSummary(Long orderId, List<OrderItemRequest> items) {
        orderItemRepository.saveAll(OrderItem.from(orderId, items));
        orderSummaryRepository.save(OrderSummary.created(orderId, items.size()));
    }
}
""",
            },
            "expected_findings": [
                {
                    "rule_id": "J-16",
                    "severity": "high",
                    "expected_issue": "Diff 把訂單主檔、明細與彙總資料拆成跨檔案的多表寫入，但沒有明確交易邊界，可能造成資料不一致。",
                    "expected_evidence": "移除 @Transactional orderRepository.save orderItemRepository.saveAll orderSummaryRepository.save",
                    "expected_recommendation": "把同一筆訂單的主檔、明細與彙總寫入放回同一個本地交易內，或補上可重試 / 可補償 / 可對帳的一致性設計。",
                    "expected_filename": "orderapplicationservice.java",
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
    compact_template = case.get("template_excerpt", "").strip()
    compact_workflow = case.get("workflow_excerpt", "").strip()
    changed_files_text = ", ".join(changed_files)
    rule_ids_text = ", ".join(case.get("source_rules_under_test", []))
    no_finding_guidance = ""
    if not case.get("expected_findings"):
        no_finding_guidance = (
            "13. 若本次 diff 只修改測試或說明檔，除非變更檔本身引入明顯錯誤，否則不要對未變更的 production code 開 finding。\n"
            "14. 這種 case 不得提及未變更 production 檔名，也不要把既有測試缺口包裝成本次 diff 的正式問題。\n"
            "15. 若目前可見範圍沒有可直接確認的問題，`問題清單` 應填 `無`，並把必要的保守說明留在 `開放問題` 或 `剩餘風險`。\n"
        )
    return (
        "請依照 java-code-review skill 與本地 Java 規則，對這個 Java diff 做正式 code review。\n"
        "這是一個 diff benchmark。你不得要求額外輸入、不得要求擴大審查到未變更檔案、不得先回覆無法 review。\n"
        "你只能根據此 prompt 內提供的規則摘要、模板摘要、workflow 摘要與 git diff 完成 review。\n"
        "禁止執行任何 shell、git、rg、Get-Content、搜尋、MCP 或其他工具；不要重新讀取 workspace、SKILL.md 或 references 檔案。\n"
        "本 benchmark 的規則、模板、workflow、變更檔名與 git diff 已完整內嵌；若你打算先掃描 repo 或讀檔，請停止並直接 review。\n"
        "即使你無法讀取 workspace 或 shell，也必須直接完成 review，不可把執行環境問題當成結論。\n"
        "只審查目前 diff 中有變更的 Java 檔案，不得提到未變更檔案名稱。\n"
        f"本次 diff 中有變更的 Java 檔案只有：{changed_files_text}\n"
        f"本 case 主要檢查的本地 rule id：{rule_ids_text}。若列出相關 finding，請盡量在 `規則` 欄標出精確 rule id。\n"
        "要求：\n"
        "1. 使用繁體中文。\n"
        "2. 套用此 prompt 內嵌的本地規則摘要；這些摘要已由 references/java-rules.md 讀出。\n"
        "3. 套用此 prompt 內嵌的模板與 workflow 摘要；這些摘要已由 references/report-templates.md 與 references/review-workflow.md 讀出。\n"
        "4. 只 review 本次 diff 中有變更的 Java 檔案，不得把未變更檔案的既有問題混進 findings。\n"
        "5. 以 Compact Review Mode 輸出。\n"
        "6. 正式報告使用固定四段：`問題清單`、`審查範圍`、`開放問題`、`剩餘風險`。\n"
        "7. 第一個 top-level heading 必須是 `問題清單`，不要先寫摘要、前言或總結。\n"
        "8. `問題清單` 使用中文 Markdown 表格，欄位名稱固定為 `嚴重度 | 類型 | 信心 | 標題 | 檔案行號 | 證據 | 影響 | 修正方向`。\n"
        "8a. 若有明確對應的本地 rule id，請放在 `標題` 開頭，例如 `H-2 敏感資料直接輸出`。\n"
        "9. `類型` 只使用 `錯誤`、`資安`、`個資`、`交易`、`資料一致性`、`業務邏輯`、`測試缺口`、`可維護性`。\n"
        "9a. `類型` 每筆 finding 只選一個主類型，不要輸出複合值如 `交易 / 資料一致性`，也不要自創標籤如 `對帳`；若風險本質是對帳、補償或最終一致性，統一歸到 `資料一致性`。\n"
        "10. `信心` 只使用 `已確認`、`高度可能`、`需確認`；若上下文不足，不可把推測包裝成已確認。\n"
        "11. `證據` 只引用目前可見 diff 或必要上下文中的具體呼叫、欄位、條件或語句。\n"
        "12. `修正方向` 保持簡短、具體、可落地；不要提供完整程式碼、patch、教學文或大型重構方案。\n"
        "12a. 不要使用舊六欄表 `嚴重度 | 規則 | 位置 | 問題 | 風險 | 建議`，也不要改用 `Findings`、`Open Questions`、`Change Summary` 等英文 section。\n"
        "13. 不要改用 `Findings`、`問題摘要`、`Open Questions`、`位置`、`問題`、`建議` 等替代 section 名稱或表頭。\n"
        "14. `審查範圍` 內固定包含兩行：`- 範圍: ...` 與 `- 已審查檔案: ...`。\n"
        "15. `檔案行號` 使用純文字 `relative/path/File.java:123`，不要輸出 Markdown 連結。\n"
        "16. `開放問題` 與 `剩餘風險` 不可合併；若沒有內容，請填 `- 無`。\n"
        f"{no_finding_guidance}\n"
        "本地規則摘要：\n"
        f"{rule_excerpt}\n\n"
        "Compact Review Mode workflow 摘要：\n"
        f"{compact_workflow}\n\n"
        "Compact 正式模板摘要：\n"
        f"{compact_template}\n\n"
        "Git diff:\n"
        "```diff\n"
        f"{diff_text.strip()}\n"
        "```\n\n"
        "請直接依上面的正式模板輸出，不要自行改寫段落名稱或表格欄位。\n"
    )


def generate_cases(
    skill_root: Path,
    diff_cases_dir: Path,
    rule_sections: dict[str, str],
    source_texts: dict[str, str],
    catalog_index: dict[str, dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    notes: list[str] = []
    cases = build_diff_case_specs()
    if catalog_index:
        notes.extend(apply_catalog_fixtures(cases, catalog_index, DIFF_CATALOG_CASE_MAP))
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


def filter_cases_by_id(cases: list[dict[str, Any]], requested_case_ids: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    if not requested_case_ids:
        return cases, []

    requested = {case_id.strip() for case_id in requested_case_ids if case_id.strip()}
    filtered = [case for case in cases if case["golden_case_id"] in requested]
    found = {case["golden_case_id"] for case in filtered}
    missing = sorted(requested - found)
    notes = [f"指定的 golden case 不存在：{case_id}" for case_id in missing]
    return filtered, notes


def detect_scope_violations(
    actual_findings: list[dict[str, Any]],
    changed_files: list[str],
    allowed_context_files: list[str] | None = None,
) -> list[dict[str, Any]]:
    changed_files_lower = {name.lower() for name in changed_files}
    allowed_context_files_lower = {name.lower() for name in (allowed_context_files or [])}
    violations: list[dict[str, Any]] = []
    for actual in actual_findings:
        referenced = extract_filenames(" ".join(actual.get("raw_lines", [])))
        referenced_changed = sorted(name for name in referenced if name in changed_files_lower)
        off_scope = sorted(name for name in referenced if name not in changed_files_lower)
        if referenced_changed and off_scope and all(
            name in allowed_context_files_lower for name in off_scope
        ):
            continue
        if off_scope:
            violations.append(
                {
                    "title": actual.get("title", ""),
                    "changed_files": referenced_changed,
                    "off_scope_files": off_scope,
                }
            )
    return violations


def detect_unchanged_file_mentions(stdout: str, unchanged_files: list[str]) -> list[str]:
    normalized = stdout.lower()
    return [name for name in unchanged_files if name.lower() in normalized]


def evaluate_static_case(case: dict[str, Any], rule_sections: dict[str, str]) -> tuple[bool, str]:
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
    execution = execute_runtime_command(command_list, case_workspace, last_message_path, timeout_seconds)
    stdout_text = execution["stdout_text"]
    stderr_text = execution["stderr_text"]
    exit_code = execution["exit_code"]
    timed_out = execution["timed_out"]

    actual_findings = parse_actual_findings(stdout_text)
    expects_no_findings = not case["expected_findings"]
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
    scope_violations = detect_scope_violations(
        actual_findings,
        changed_files,
        case.get("allowed_context_files_in_findings", []),
    )
    unchanged_file_mentions = detect_unchanged_file_mentions(stdout_text, unchanged_files)
    allowed_unchanged_mentions = {
        name.lower() for name in case.get("allowed_unchanged_file_mentions", [])
    }
    if allowed_unchanged_mentions:
        unchanged_file_mentions = [
            name for name in unchanged_file_mentions if name.lower() not in allowed_unchanged_mentions
        ]
    timeout_recovered = False
    if timed_out and actual_findings and template_compliance and workflow_compliance:
        timed_out = False
        exit_code = 0
        timeout_recovered = True
    precision = 0.0 if not actual_findings else len(matched_findings) / len(actual_findings)
    recall = 1.0 if expects_no_findings else len(matched_findings) / len(case["expected_findings"])
    quality_pass = (
        exit_code == 0
        and not missed_findings
        and not must_not_violations
        and (not expects_no_findings or not actual_findings)
    )
    scope_pass = not scope_violations and not unchanged_file_mentions
    format_pass = template_compliance and workflow_compliance
    overall_pass = quality_pass and scope_pass and format_pass

    if timed_out:
        reason = f"runtime mode 執行逾時，case 已記錄為失敗；timeout={timeout_seconds}s。"
    elif timeout_recovered:
        reason = "runtime mode 已輸出完整最終報告；雖然原行程逾時，但已根據 last-message 成功恢復結果。"
    elif expects_no_findings and actual_findings:
        reason = "runtime mode 本 case 預期零 findings，但實際輸出了 review finding。"
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
        "command": subprocess.list2cmdline(execution["final_command_list"]),
        "working_directory": str(case_workspace),
        "exit_code": exit_code,
        "stdout": stdout_text,
        "stderr": stderr_text,
        "runtime_attempt_count": execution["attempt_count"],
        "retried_on_spawn_setup": execution["retried_on_spawn_setup"],
        "used_spawn_safe_retry": execution["used_spawn_safe_retry"],
        "timeout_recovered": timeout_recovered,
        "passed": overall_pass,
        "reason": reason,
    }


def gate_b_status(cases: list[dict[str, Any]], rule_sections: dict[str, str]) -> tuple[str, list[str]]:
    issues: list[str] = []
    if not cases:
        return "fail", ["diff golden cases 為空。"]
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


def write_progress_snapshot(
    output_dir: Path,
    results: list[dict[str, Any]],
    total_cases: int,
    validation_mode: str,
) -> None:
    progress_path = output_dir / "golden_progress.json"
    golden_results_path = output_dir / "golden_results.jsonl"
    write_jsonl(golden_results_path, results)
    write_json(
        progress_path,
        {
            "validation_mode": validation_mode,
            "completed_cases": len(results),
            "total_cases": total_cases,
            "completed_case_ids": [result["golden_case_id"] for result in results],
            "passed_case_ids": [result["golden_case_id"] for result in results if result.get("passed")],
            "failed_case_ids": [result["golden_case_id"] for result in results if not result.get("passed")],
        },
    )


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
    benchmark_catalog, catalog_notes = load_benchmark_catalog(skill_root)
    benchmark_layer = get_benchmark_layer(benchmark_catalog, "diff_pr")
    benchmark_case_index = build_benchmark_case_index(benchmark_layer)
    java_rules_text = source_texts.get("references/java-rules.md", "")
    rule_sections = parse_rule_sections(java_rules_text) if java_rules_text else {}
    cases, case_notes = generate_cases(skill_root, diff_cases_dir, rule_sections, source_texts, benchmark_case_index)
    case_notes.extend(annotate_cases_with_catalog(cases, benchmark_case_index, DIFF_CATALOG_CASE_MAP))
    cases, filtered_case_notes = filter_cases_by_id(cases, args.case_id)
    case_notes.extend(filtered_case_notes)

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
    total_cases = len(cases)
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
                "catalog_case_ids": case.get("catalog_case_ids", []),
                "catalog_primary_signals": case.get("catalog_primary_signals", []),
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
                "catalog_case_ids": case.get("catalog_case_ids", []),
                "catalog_primary_signals": case.get("catalog_primary_signals", []),
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
        write_progress_snapshot(output_dir, results, total_cases, validation_mode)

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
    catalog_alignment = summarize_catalog_alignment(cases)

    summary: dict[str, Any] = {
        "working_directory": str(skill_root),
        "command": invocation_command,
        "exit_code": 0,
        "scenario": "diff_pr",
        "validation_mode": validation_mode,
        "benchmark_catalog_version": benchmark_catalog.get("version"),
        "benchmark_catalog_layer": "diff_pr",
        "benchmark_catalog_case_count": len(benchmark_case_index),
        "catalog_alignment": catalog_alignment,
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
        "notes": manifest_notes + catalog_notes + case_notes + runtime_notes + gate_a_notes + gate_b_notes + gate_c_notes + gate_d_notes,
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
