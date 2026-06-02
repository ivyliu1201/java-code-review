# Java Code Review Skill Status Report

日期：`2026-05-26`

這份文件用來記錄 `java-code-review` skill 目前已完成的整理、benchmark 驗證結果、coverage audit 與下一步，避免對話中斷後失去上下文。

> 注意：這是一份 `2026-05-26` 的歷史快照。後續已新增 runnable fixture 與腳本支援，包含 `exception-swallow-holdout-01`、`hashmap-query-holdout-01`、`test-only-change-diff-01`、`multi-file-order-diff-01`；目前最新可執行案例請以 `benchmark_catalog.json`、`README.md` 與各 benchmark README 為準。

## 1. 目前狀態

- skill runtime 已從測試導向污染中收斂回 core Java review 目的。
- 正式中文輸出已固定成 canonical 格式：
  1. `問題清單`
  2. `審查範圍`
  3. `開放問題`
  4. `剩餘風險`
- `single-file` 與 `diff / PR` benchmark 已可做 runtime 驗證。
- benchmark 已改成 catalog-driven 架構，核心定義在 [benchmark_catalog.json](./benchmark_catalog.json)。
- `large-codebase` benchmark 架構已建立，但 runnable coverage 仍偏薄。

## 2. 重要提交

近期關鍵 commit：

1. `889317c` `Refocus skill runtime and split validation benchmarks`
2. `1720ee8` `Refine java review rules for large-project reviews`
3. `d5fa718` `Make benchmark catalog drive runnable validation cases`
4. `f327ef7` `Add runnable benchmark cases and runtime coverage`
5. `0eb032b` `Align canonical review output contract`
6. `86e2bbd` `Stabilize diff review output contract`

## 3. 最新驗證結果

### 3.1 Single-file Holdout

結果檔：
- [golden_summary.json](./results/golden_tests_runtime_holdout_v5/golden_summary.json)

摘要：
- `passed_golden_cases = 7`
- `failed_golden_cases = 0`
- `quality_passed_golden_cases = 7`
- `format_passed_golden_cases = 7`
- `workflow_failures = []`

判讀：
- `single-file holdout` 已確認全過。
- canonical 中文表格輸出在 compact 單檔路徑已穩定。

### 3.2 Diff / PR Runtime

結果檔：
- [golden_summary.json](./results/diff_golden_tests_runtime_v6/golden_summary.json)

摘要：
- `passed_golden_cases = 6`
- `failed_golden_cases = 0`
- `quality_passed_golden_cases = 6`
- `scope_passed_golden_cases = 6`
- `format_passed_golden_cases = 6`
- `template_failures = []`
- `workflow_failures = []`

判讀：
- `diff / PR` runtime 已確認全過。
- 目前 diff review 已不再卡在 `Findings` / `問題摘要` / 英文 section 漂移。

### 3.3 Single-file Baseline

目前狀態：
- 這一輪尚未補最新 runtime 重跑確認。

判讀：
- 不能直接宣稱「single baseline 也已最新確認通過」。
- 目前明確已實際確認的是 `single holdout` 與 `diff runtime`。

### 3.4 Large-codebase Runtime

目前狀態：
- large-codebase benchmark 架構存在。
- runnable case 目前只有 `large-codebase-01` 這一組主案例。

相關檔案：
- [README_large_benchmark.md](./README_large_benchmark.md)
- [run_large_codebase_benchmarks.py](./run_large_codebase_benchmarks.py)

判讀：
- 已具備「往大專案測試前進」的 benchmark 骨架。
- 但 large-codebase coverage 還不足以說已成熟完成。

## 4. Coverage Audit 總覽

這份 audit 以 A ~ M 規則為單位，區分：
- `runnable`：已有 fixture，可直接跑 benchmark
- `concept-only`：有 catalog case 設計，但尚未提供 fixture
- `uncovered`：完全沒有 benchmark coverage

### 4.1 區塊級摘要

| 區塊 | 規則總數 | runnable 已覆蓋 | concept-only | 未覆蓋 |
|---|---:|---:|---:|---:|
| `0` | 1 | 1 | 0 | 0 |
| `A` | 12 | 0 | 0 | 12 |
| `B` | 5 | 2 | 0 | 3 |
| `C` | 4 | 0 | 0 | 4 |
| `D` | 4 | 0 | 0 | 4 |
| `E` | 7 | 0 | 0 | 7 |
| `F` | 3 | 1 | 0 | 2 |
| `G` | 8 | 0 | 0 | 8 |
| `H` | 5 | 1 | 0 | 4 |
| `I` | 6 | 0 | 0 | 6 |
| `J` | 18 | 5 | 1 | 12 |
| `K` | 4 | 0 | 2 | 2 |
| `L` | 5 | 2 | 0 | 3 |
| `M` | 4 | 2 | 0 | 2 |

### 4.2 已有 Runnable Coverage 的規則

| rule | runnable case |
|---|---|
| `0-1` | `large-codebase-01` workflow context |
| `B-1` | `sf-null-safe-equals-01`, `diff-null-safety-01` |
| `B-5` | `sf-long-method-01` |
| `F-3` | `sf-performance-logging-01`, `diff-performance-logging-01` |
| `H-2` | `sf-security-masking-01`, `diff-security-scope-01`, `large-codebase-01` context |
| `J-1` | `sf-state-transition-01` |
| `J-6` | `sf-idempotency-01` |
| `J-7` | `sf-transaction-boundary-01`, `diff-transaction-01` |
| `J-10` | `sf-time-boundary-01` |
| `L-1` | `sf-transaction-boundary-01`, `diff-transaction-01`, `large-codebase-01` context |
| `L-3` | `sf-dto-entity-boundary-01`, `diff-maintainability-01`, `large-codebase-01` context |
| `M-1` | `diff-cache-scope-01` |
| `M-4` | `sf-cache-sensitive-data-01`, `diff-cache-scope-01`, `large-codebase-01` context |

### 4.3 只有 Concept-only，尚未 Runnable 的規則

| rule | concept-only case |
|---|---|
| `K-1` | `diff-test-only-change-01` |
| `K-2` | `diff-test-only-change-01` |
| `J-16` | `diff-multi-file-order-01` |

### 4.4 完全沒有 Coverage 的高優先區

目前完全沒有 benchmark coverage 的大區：

- `A` Naming & Constants
- `C` Collections & Generics
- `D` Concurrency & Threading
- `E` Exception & Resource Safety
- `G` DB / SQL / ORM Safety
- `I` Misc / Style / Regex / Random

其中若以「大專案 backend review」為優先，最值得先補的是：

1. `G` 區
2. `E` 區
3. `J` 區尚未覆蓋的高風險規則
4. `L-2 / L-4 / L-5`
5. `K-3 / K-4`

## 5. 對「能否邁向大專案 benchmark」的判斷

### 已具備的基礎

- `single-file` 已有可用的 quality benchmark。
- `diff / PR` 已有可用的 quality + scope + format benchmark。
- canonical 中文表格正式輸出已被 runtime 驗證穩定。
- benchmark 已是 catalog-driven，不是一次性腳本。

### 尚未補齊的部分

- `single baseline` 這一輪尚未補最新 runtime 確認。
- `diff` 目前尚未拆出 `baseline / holdout`。
- `large-codebase` runnable case 只有 1 組。
- `G / E / J / L / K` 的 coverage 還不夠厚。

### 結論

- 可以說已經「邁向大專案 benchmark」。
- 但不能說 large-codebase benchmark 已成熟完成。
- 正確說法是：
  - `small / medium review benchmark` 已很接近正式可用
  - `large-project benchmark` 已有架構，但 coverage 仍需擴充

## 6. 建議下一步

建議順序：

1. 補 `single-file baseline` 最新 runtime 確認。
2. 補第一批 `G` 區 runnable cases。
3. 補第一批 `E` 區 runnable cases。
4. 把 `J-16`、`K-1`、`K-2` 從 concept-only 補成 runnable。
5. 補 `large-codebase` runnable cases：
   - `lg-batch-planning-01`
   - `lg-ledger-progress-01`
   - `lg-pending-disclosure-01`
   - `lg-cross-module-risk-01`
6. 規劃 `diff baseline / diff holdout` 拆組。

## 7. 明天若要直接接續，可用的指令或請求

可直接對 Codex 下這類請求：

- `幫我補 single-file baseline runtime 確認`
- `幫我從 G 區開始補 runnable benchmark cases`
- `幫我把 J-16 / K-1 / K-2 補成 runnable diff cases`
- `幫我擴充 large-codebase runnable benchmark`
- `幫我做 diff holdout 拆組設計`
- `幫我重跑 single + diff + large benchmark 並整理 summary`
