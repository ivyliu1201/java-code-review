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
- `敏感資料直接輸出`
- `交易邊界不正確`
- `Controller 直接承載核心業務邏輯`
- `缺少冪等保護`

建議描述方式：

- `違反本地規則 A-5，因為 static final 常數未使用全大寫底線命名`
- `違反本地規則 H-2，因為 API 直接回傳完整敏感欄位`
- `違反本地規則 L-1，因為在本地交易內直接呼叫外部系統`

如果修法很直接，可附上短版替代範例：

```java
private String userName;
static final int TIMEOUT_MILLIS = 5000;
```

## 一般 Review 模板

使用者未要求正式報告，且範圍符合 Compact Review Mode 時使用。

```text
審查範圍
- 範圍: [檔案集合 / diff / review 範圍]
- 已審查檔案: [file A], [file B]

問題清單
| 嚴重度 | 標題 | 規則 | 檔案行號 | 影響 | 修正方向 |
| --- | --- | --- | --- | --- | --- |
| 嚴重 | [若無則填 無] | [rule id 或規則類別] | [file:line] | [影響] | [修正方向] |
| 主要 | [若無則填 無] | [rule id 或規則類別] | [file:line] | [影響] | [修正方向] |
| 次要 | [若無則填 無] | [rule id 或規則類別] | [file:line] | [影響] | [修正方向] |
| 建議 | [若無則填 無] | [rule id 或規則類別] | [file:line] | [影響] | [修正方向] |

進度
- [若已完成可省略；若未完成，列出已 review / 尚未 review / 下一步]

開放問題
- [問題；若無則可填 無]

剩餘風險
- [風險；若無則可填 無]
```

## Compact 正式 Review 模板

啟用 Compact Review Mode 且使用者要求正式審查報告時使用。保留所有欄位；無內容時填 `無`。

```text
審查範圍
- 範圍: [檔案集合 / diff / 小範圍目標]
- 已審查檔案: [file A], [file B]

問題清單
| 嚴重度 | 標題 | 規則 | 檔案行號 | 影響 | 修正方向 |
| --- | --- | --- | --- | --- | --- |
| 嚴重 | [標題或無] | [rule id 或規則類別] | [file:line] | [用一到兩句說明影響] | [簡短替代寫法或修正方向] |
| 主要 | [標題或無] | [rule id 或規則類別] | [file:line] | [用一到兩句說明影響] | [簡短替代寫法或修正方向] |
| 次要 | [標題或無] | [rule id 或規則類別] | [file:line] | [用一到兩句說明影響] | [簡短替代寫法或修正方向] |
| 建議 | [標題或無] | [rule id 或規則類別] | [file:line] | [用一到兩句說明影響] | [簡短替代寫法或修正方向] |

開放問題
- [問題；若無則填 無]

剩餘風險
- [風險；若無則填 無]
```

## Large Codebase Review Mode 模板

啟用 Large Codebase Review Mode 時一律使用。保留 `審查範圍`、`目前批次`、`審查台帳`、`批次摘要`、依嚴重度分類的 findings、`進度`、`開放問題`、`剩餘風險` 與 `續跑提示`。

```text
審查範圍
- 範圍: [資料夾 / staged changes / 檔案集合]
- Java 檔案總數: [總數]
- Inventory order: [排序方式，例如 path asc]
- File inventory: [完整清單或編號範圍]
- Excluded: [排除項目與理由]
- Batch plan: [例如 1/4, 2/4, 3/4, 4/4]

目前批次
- Batch: [第幾批 / 共幾批]
- Reviewed files: [file A], [file B]

審查台帳
- Reviewed: [清單]
- Pending: [清單]
- Excluded: [清單與理由]

批次摘要
- [本批摘要]
- [高優先問題摘要]

高優先問題
| 嚴重度 | 標題 | 檔案行號 | 一句話摘要 |
| --- | --- | --- | --- |
| 嚴重 | [finding 編號或標題] | [file:line] | [一句話摘要] |
| 主要 | [finding 編號或標題] | [file:line] | [一句話摘要] |

詳細問題
| 嚴重度 | 標題 | 規則 | 檔案行號 | 影響 | 修正方向 |
| --- | --- | --- | --- | --- | --- |
| 嚴重 | [標題或無] | [rule id 或規則類別] | [file:line] | [用一到兩句說明影響] | [簡短替代寫法或修正方向] |
| 主要 | [標題或無] | [rule id 或規則類別] | [file:line] | [用一到兩句說明影響] | [簡短替代寫法或修正方向] |
| 次要 | [標題或無] | [rule id 或規則類別] | [file:line] | [用一到兩句說明影響] | [簡短替代寫法或修正方向] |
| 建議 | [標題或無] | [rule id 或規則類別] | [file:line] | [用一到兩句說明影響] | [簡短替代寫法或修正方向] |

進度
- Reviewed so far: [已 review 檔案或數量]
- Remaining: [尚未 review 檔案或下一批起點]
- Next output: [若內容過長，依同批次分 part 續出]

開放問題
- [問題；若無則填 無]

剩餘風險
- [風險；若無則填 無]

續跑提示
- [提供可直接續跑的 prompt]
```
