<div align="center">

# Java Code Review Skill

依本地 Java 規範，為 Codex 提供可追溯、可分批且不漏檔的程式碼審查流程。

[![Codex Skill](https://img.shields.io/badge/Codex-Skill-111827?style=flat-square)](SKILL.md)
[![Review Target](https://img.shields.io/badge/Review_Target-Java-E76F00?style=flat-square&logo=openjdk&logoColor=white)](references/java-rules.md)
[![Output](https://img.shields.io/badge/Output-%E7%B9%81%E9%AB%94%E4%B8%AD%E6%96%87-2563EB?style=flat-square)](references/report-templates.md)

</div>

## 專案簡介

`java-code-review` 是一個給 Codex 使用的 Java 程式審查 skill。它把完整規則、審查流程與報告格式分開管理，支援單檔、diff、PR 與大型 codebase review，也能在產生或重構 production Java 程式碼時套用相同規範。

規則不是抽樣提示：審查前必須以 UTF-8 讀取正式規則來源，並依範圍選擇 Compact 或 Large Codebase Review Mode。未完成全部 inventory 前，不得宣稱整體審查完成。

## 核心能力

- **本地規範優先**：依 [`references/java-rules.md`](references/java-rules.md) 審查，不只檢查一般 style。
- **完整範圍追蹤**：要求列出 scope、reviewed files、排除項目與剩餘進度。
- **大小範圍分流**：小範圍一次完成；大型範圍建立 inventory、batch 與 ledger。
- **一致的正式報告**：使用固定嚴重度與八欄問題清單，讓證據、影響與修正方向可追溯。
- **審查與產碼共用規則**：修改或產生 Java 程式碼時，沿用相同命名、安全與結構要求。
- **不以測試取代規格**：驗證腳本與 benchmark 用來檢查 skill，不是 runtime 規格來源。

## 快速開始

### 1. 安裝

將 repository 放到 Codex skills 目錄：

```powershell
git clone https://github.com/ivyliu1201/java-code-review.git "$env:USERPROFILE\.codex\skills\java-code-review"
```

若已下載原始碼，也可以直接將整個資料夾放到：

```text
%USERPROFILE%\.codex\skills\java-code-review
```

### 2. 觸發 skill

在對話中明確指定：

```text
請用 $java-code-review 依本地 Java 規範審查這次修改。
```

或使用預設英文 prompt：

```text
Use $java-code-review to review this Java change against the local Java rules.
```

### 3. 指定範圍

可提供單一檔案、git diff、PR 變更、staged changes 或整個 Java 專案。Skill 會依檔案數量與 context 容量選擇對應模式。

## 審查流程

```text
確認範圍
   ↓
讀取 SKILL.md 與正式 Java 規則
   ↓
選擇 Compact / Large Codebase Review Mode
   ↓
逐檔審查並記錄 findings
   ↓
依正式模板輸出結果與剩餘風險
```

| 模式 | 適用情境 | 必要要求 |
|---|---|---|
| **Compact Review Mode** | Java 檔案不超過 5 個，且內容能在單次 context 中完整審查 | 列出 scope 與 reviewed files；不可抽樣或跳檔 |
| **Large Codebase Review Mode** | 超過 5 個 Java 檔、整個資料夾、staged changes 或無法一次完整審查的範圍 | 建立穩定排序的 inventory；每批最多 10 個檔案；持續維護 ledger |

即使沒有 findings，也必須明確說明已審查範圍，並列出剩餘風險或測試缺口。

## 規則範圍

正式規則涵蓋：

- Naming、constants、magic values 與 enum。
- OOP、collections、generics 與 concurrency。
- Exceptions、resource management、logging 與 observability。
- SQL、ORM、database、cache 與 distributed safety。
- Security、authorization、資料保護與輸入輸出邊界。
- Business logic、交易一致性、冪等、補償與批次處理。
- Tests、Spring、API contract、documentation 與 service orchestration。

[`references/java-rule-index.md`](references/java-rule-index.md) 可用來快速定位章節，但不能取代正式規則原文。

## 報告格式

繁體中文正式報告預設使用以下嚴重度：

| 等級 | 用途 |
|---|---|
| `嚴重` | 可能造成重大安全、資料或核心業務風險 |
| `主要` | 明確影響正確性、維護性或既有契約 |
| `次要` | 局部品質問題或低風險缺陷 |
| `建議` | 非必要但有價值的改善 |

問題清單固定包含：

```text
嚴重度 | 類型 | 信心 | 標題 | 檔案行號 | 證據 | 影響 | 修正方向
```

使用者要求英文時，可改用 `Critical`、`Major`、`Minor`、`Suggestions`。

## 專案結構

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── java-rules.md
│   ├── java-rule-index.md
│   ├── report-templates.md
│   └── review-workflow.md
└── scripts/
    ├── benchmark_catalog.json
    ├── validate_skill.py
    ├── run_golden_tests.py
    ├── run_diff_golden_tests.py
    ├── run_large_codebase_benchmarks.py
    └── demo_small_project/
```

| 路徑 | 用途 |
|---|---|
| [`SKILL.md`](SKILL.md) | 觸發條件、必做規則、審查與產碼契約 |
| [`agents/openai.yaml`](agents/openai.yaml) | OpenAI agent 顯示資訊與預設 prompt |
| [`references/java-rules.md`](references/java-rules.md) | 完整 Java 本地規則，也是最高優先規則來源 |
| [`references/review-workflow.md`](references/review-workflow.md) | Compact 與 Large Codebase Review Mode 流程 |
| [`references/report-templates.md`](references/report-templates.md) | Finding 標題與正式報告模板 |
| [`scripts/`](scripts/) | 靜態驗證、golden tests 與 benchmark 工具 |

## 驗證

使用官方 skill 驗證腳本檢查基本格式：

```powershell
$env:PYTHONUTF8='1'
python C:\Users\fanny\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\fanny\.codex\skills\java-code-review
```

預期輸出：

```text
Skill is valid!
```

Repository 內另將驗證分為三層：

1. **Single-file rule benchmark**：檢查單一規則是否能穩定命中。
2. **Diff / PR scope benchmark**：檢查 findings 是否維持在變更範圍。
3. **Large-codebase workflow benchmark**：檢查 inventory、batch、ledger、進度與續跑提示。

## 使用限制

- 審查、產碼或重構 Java 程式碼前，必須以 UTF-8 讀取 `references/java-rules.md`。
- 若規則檔無法讀取，不得宣稱結果符合本地 Java 規範。
- 預設只做 review；只有使用者明確要求時才修改程式碼。
- 終端顯示亂碼時，應先排查顯示編碼，不得直接覆寫規則檔。
- 大型審查不得抽樣、跳檔，或在 inventory 尚未完成時宣稱全部完成。

