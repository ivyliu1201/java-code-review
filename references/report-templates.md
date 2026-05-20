# 報告模板

格式化 `java-code-review` 的 Java 審查輸出時使用此參考文件。

## 模板選擇

- 啟用 Large Codebase Review Mode 時，一律使用 Large Codebase Review Mode 模板。
- 啟用 Compact Review Mode 且使用者要求正式報告時，使用 Compact Review Mode 正式模板。
- 啟用 Compact Review Mode 且使用者未要求正式報告時，使用一般 review 模板。
- 可盡量配合使用者指定格式，但不得省略必要的範圍、進度、完成狀態與風險資訊。

## Finding 標題

使用直接、可定位問題類型的 finding 標題，例如：

- `命名規則違反`
- `常數規則違反`
- `package/class/method 命名不一致`
- `布林命名不一致`
- `magic value 應改為常數或 enum`

建議描述方式：

- `違反本地規則 A-1，因為識別字以 '_' 結尾`
- `違反本地規則 A-5，因為 static final 常數未使用全大寫底線命名`
- `違反本地規則 A-10，因為 status 值以 magic number 表示`

如果修法很直接，可附上短版替代範例：

```java
private String userName;
static final int TIMEOUT_MILLIS = 5000;
```

## 一般 Review 模板

使用者未要求正式報告，且範圍符合 Compact Review Mode 時使用。

```text
Review Scope
- Scope: [檔案集合 / diff / review 範圍]
- Reviewed files: [file A], [file B]

Findings
Critical
- [...]

Major
- [...]

Minor
- [...]

Suggestions
- [...]

Progress
- [若已完成可省略；若未完成，列出已 review / 尚未 review / 下一步]

Open questions
- [問題；若無則可填 None]

Residual risks
- [風險；若無則可填 None]
```

## Compact 正式 Review 模板

啟用 Compact Review Mode 且使用者要求正式審查報告時使用。保留所有欄位；無內容時填 `None`。

```text
Review Scope
- Scope: [檔案集合 / diff / 小範圍目標]
- Reviewed files: [file A], [file B]

Findings
Critical
1. [標題] - [file:line]
Rule: [rule id 或規則類別]
Why: [影響]
Suggested fix: [修正方向]

Major
1. [...]

Minor
1. [...]

Suggestions
1. [...]

Open questions
- [問題；若無則填 None]

Residual risks
- [風險；若無則填 None]
```

## Large Codebase Review Mode 模板

啟用 Large Codebase Review Mode 時一律使用。保留 `Review Scope`、`Current Batch`、`Review ledger`、`Batch summary`、依嚴重度分類的 findings、`Progress`、`Open questions`、`Residual risks` 與 `Continuation prompt`。

`High priority findings` 只放 Critical 與 Major 摘要；完整內容放在 `Detailed findings`。

```text
Review Scope
- Scope: [資料夾 / staged changes / 檔案集合]
- Total Java files: [總數]
- Inventory order: [排序方式，例如 path asc]
- File inventory: [完整清單或編號範圍]
- Excluded: [排除項目與理由]
- Batch plan: [例如 1/4, 2/4, 3/4, 4/4]

Current Batch
- Batch: [第幾批 / 共幾批]
- Reviewed files: [file A], [file B]

Review ledger
- Reviewed: [清單]
- Pending: [清單]
- Excluded: [清單與理由]

Batch summary
- [本批摘要]
- [高優先問題摘要]

High priority findings
Critical
1. [finding 編號或標題] - [一句話摘要，完整內容見 Detailed findings]

Major
1. [finding 編號或標題] - [一句話摘要，完整內容見 Detailed findings]

Detailed findings
Critical
1. [標題] - [file:line]
Rule: [rule id 或規則類別]
Why: [用一到兩句說明影響]
Suggested fix: [簡短替代寫法或修正方向]

Major
1. [...]

Minor
1. [...]

Suggestions
1. [...]

Progress
- Reviewed so far: [已 review 檔案或數量]
- Remaining: [尚未 review 檔案或下一批起點]
- Next output: [若內容過長，依同批次分 part 續出]

Open questions
- [問題；若無則填 None]

Residual risks
- [風險；若無則填 None]

Continuation prompt
- [提供可直接續跑的 prompt]
```
