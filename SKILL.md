---
name: java-code-review
description: 當使用者要求依照本地 Java 規範進行 code review、命名/常數檢查、重構，或產生正式 production Java 程式碼時使用。套用規則前必須先以 UTF-8 讀取 references/java-rules.md。
---

# Java 程式審查

當使用者要求依照本地 Java 規範進行程式審查、產生程式碼或重構時，使用這個 skill。

## 核心規則

1. 在審查、產碼或重構任何 Java 程式碼之前，先以 UTF-8 讀取 `references/java-rules.md`。
2. `references/java-rules.md` 是最高優先規則來源；只要本地規則比通用 Java 慣例更具體，就以本地規則為準。
3. 本地規則同時適用於 Java code review、Java 程式碼產生與 Java 重構。
4. 如果 framework 或 library 慣例與本地規則衝突，必須明確指出衝突點，並在放寬規則前說明取捨理由。
5. 保持原始規則意圖，不可默默弱化、改寫或重新詮釋硬性規則。
6. 預設只做 review，不修改程式碼；只有在使用者明確要求修改時，才可提出或實作修正。
7. 預設輸出語言使用繁體中文；若使用者明確指定其他語言，才可改用該語言。

## 規則載入與失敗處理

- 一律以 UTF-8 讀取 `references/java-rules.md`。
- 如果終端輸出看起來像亂碼，優先假設是顯示編碼錯誤，不是來源檔案損壞。
- 除非使用者明確要求轉碼，否則不要把規則檔改寫成其他編碼。
- 如果 `references/java-rules.md` 無法讀取、讀取失敗或內容不完整，不得宣稱已套用本地規則。
- 發生讀取失敗時，必須明確說明目前無法依本地規則完成正式審查或正式產碼。
- 若使用者仍要求繼續，可改以通用 Java 慣例進行暫時性審查或產碼，但必須明確標示「未套用本地規則」，且不得宣稱結果符合本地 Java 規範。

## 審查原則

1. 先檢查 Java diff 或目標檔案內容。
2. 以本地規則文件為主進行違規檢查，不要只做通用 style review。
3. findings 優先順序如下：
   - 違規造成的正確性問題或 production 風險
   - 可維護性或可讀性下降
   - 一致性與命名問題
4. 若輸入內容包含檔案路徑、diff line 或可定位行號，finding 必須附上檔案與行號。
5. 單一 finding 預設使用精簡格式，只保留標題、規則、檔案行號、影響與修正方向，避免冗長敘述。
6. 如果沒有發現問題，要明確寫出沒有 findings，並補充剩餘風險或測試缺口。
7. finding 必須有具體依據，例如程式碼片段、diff、本地規則條文、可清楚說明的風險鏈；不可只憑偏好硬列問題。
8. 缺少必要上下文時，不可把推測當成確定 finding；應改列為 `Open Questions` 或 `Residual Risks`。

## Severity 定義

- `Critical`: 明確的正確性、安全性、資料損壞、交易流程錯誤，或高機率 production 事故風險。
- `Major`: 明確規則違反、邏輯脆弱、可維護性重大缺陷，或高風險但未必立即造成事故的問題。
- `Minor`: 一致性、命名、可讀性、結構細節等非關鍵問題。
- `Suggestions`: 非必要但合理的改善建議。

## Review Modes

### Compact Review Mode

若 Java 檔案數小於等於 5，且所有 diff / file content 可在單次 context 中完整審查，可使用 Compact Review Mode。

- 仍需列出 review scope 與 reviewed files。
- 仍不可抽樣、不可跳檔、不可假裝完成。
- 若 review 過程發現內容過大或無法一次完整涵蓋，必須升級為 Large Codebase Review Mode。

## Large Codebase Review Mode

超過 5 個 Java 檔、整個資料夾、staged changes、壓縮包、多檔混合來源，或任何無法一次完整審查的範圍，必須啟用 Large Codebase Review Mode。

1. 開始 review 前，必須先建立 Java file inventory，不可直接抽樣閱讀。
2. inventory 至少要列出：
   - review scope
   - Java 檔案總數
   - 完整 Java 檔案清單
   - 排除項目與排除理由
   - 預計批次計畫
3. inventory 中的 Java 檔案必須以固定順序編號，建議依路徑排序；後續批次必須沿用同一順序，不可每一批重新挑選。
4. 每一批最多 review 10 個 Java 檔，建議以 5 到 10 個檔案為一批；如果檔案明顯偏大、類別複雜、單批內容可能超出可用 context、單批預期 findings 過多、單檔問題密集，或輸出報告可能過長，必須主動縮小批次。
5. 除非使用者明確允許抽樣，否則不可抽樣，不可跳檔，不可只挑重點檔案看。
6. 只有在 inventory 中列出的每個檔案都已完成 review，才可宣稱全部 review 完成。
7. 如果 review 對象包含 staged changes，仍要先列出 staged Java file inventory，再安排批次。
8. 如果 review 對象是壓縮包、貼上的多檔程式碼或混合來源，也要先整理出可追蹤的 Java 檔案清單後再開始。
9. 除非使用者明確指定，否則不得自行排除 production Java 檔；若排除 generated code、third-party vendored code、build output 或其他非審查目標，必須明列理由。
10. 建立 inventory 後，必須先輸出 inventory 與目前批次，再輸出 batch findings；不得省略 batch report，或只在最後輸出整體結果。
11. 若同一回合 context 仍足夠，可連續輸出多個 batch report；但必須保留明確批次邊界，不可把多批 findings 混成單一總結。

## 批次、完成條件與上下文

Large Codebase Review Mode 下，每一批都必須輸出 batch report。

1. 先列出本批實際 review 的檔案清單。
2. findings 必須依 `Critical`、`Major`、`Minor`、`Suggestions` 分類輸出。
3. 若某個嚴重度沒有問題，應明確標示 `None` 或等價說法，避免歧義。
4. 每批結尾必須列出剩餘未 review 檔案，或至少清楚指出下一批起點與預計續看範圍。
5. 不可用模糊說法帶過，例如「其餘大致正常」或「大部分已檢查完」。
6. 若完整 findings 過長，先輸出 batch summary 與高優先問題，再續出 detailed findings；不可因篇幅省略未列出的問題。
7. 若同一批報告仍過長，可拆成 `Part 1`、`Part 2`、`Part 3` 等多段輸出；不得跨批混寫，且每一段都要標示同一批次編號與目前 part。若回覆上限允許，應連續輸出至該批報告完成。
8. 若一次無法 review 完所有 Java 檔，必須停在批次邊界，不可假裝已完成。
9. 停止時必須明確列出已 review 檔案、尚未 review 檔案、目前停在哪一批、下一批起點與 continuation prompt。
10. 如果 context 不足以支撐完整結論，必須直接說明仍未完成，而不是輸出看似完整的總結。
11. 只有在所有批次都完成後，才可輸出 final summary。
12. 輸出 final summary 前，必須先對照 inventory 確認每個檔案都已標記為 `reviewed`、`pending` 或 `excluded`；若仍有任何 `pending` 檔案，必須改為輸出未完成清單與目前進度，不可輸出完成版總結。
13. final summary 至少要包含總 Java 檔案數、已 review 檔案數、`Critical` / `Major` / `Minor` / `Suggestions` 統計、最高風險檔案、Top priority fixes。

## 回應契約

預設使用以下回應原則：

1. 先列 findings，並依嚴重度與使用者影響排序。
2. 每一筆 finding 盡量包含：短標題、規則類別或 rule id、檔案與行號、影響、修正方向。
3. 如果沒有 findings，要先明講，再做摘要。
4. 變更摘要只能作為次要資訊，不可蓋過 findings。
5. 若啟用 Compact Review Mode，回應中至少要交代 review scope 與 reviewed files。
6. 若啟用 Large Codebase Review Mode，回應中必須先交代 scope、inventory 摘要、review ledger、目前批次與整體進度。
7. 若缺少上下文，不可把推測包裝成 finding；應改寫在 `Open Questions` 或 `Residual Risks`。
8. 如果尚未 review 完所有檔案，回應中必須明確寫出未完成狀態，不可暗示全面完成。
9. 若使用者指定輸出格式或只要求特定嚴重度，應盡量配合；但不得違反核心規則、完成條件或未完成狀態揭露要求。
10. 若使用者未要求正式審查報告，預設使用精簡的一般 review 回覆；但仍需保留 scope、reviewed files 或 batch 範圍、依嚴重度分類的 findings，以及必要的 `Open Questions` / `Residual Risks` / 進度資訊。
11. 除非使用者明確指定其他語言，所有 review 報告、batch report、final summary、open questions、residual risks 與 continuation prompt 一律使用繁體中文撰寫。

Finding 標題可使用以下類型：

- `命名規則違反`
- `常數規則違反`
- `package/class/method 命名不一致`
- `布林命名不一致`
- `magic value 應改為常數或 enum`

建議使用這類描述方式：

- `違反本地規則 A-1，因為識別字以 '_' 結尾`
- `違反本地規則 A-5，因為 static final 常數未使用全大寫底線命名`
- `違反本地規則 A-10，因為 status 值以 magic number 表示`

如果修法很直接，可以附短版替代範例：

```java
private String userName;
static final int TIMEOUT_MILLIS = 5000;
```

## 輸出模式與模板

模板選擇規則：

1. 若啟用 Large Codebase Review Mode，必須使用 Large Codebase Review Mode 模板；即使使用者未要求正式審查報告，也不得省略 inventory、batch、review ledger、progress 與 continuation prompt。
2. 若啟用 Compact Review Mode，且使用者要求正式審查報告，使用 Compact Review Mode 模板。
3. 若啟用 Compact Review Mode，且使用者未要求正式審查報告，使用一般 review 回覆模板。
4. 若使用者指定自訂格式，應盡量配合；但不得省略對應 mode 的必要資訊。

若使用者未要求正式審查報告，預設使用以下一般 review 回覆模板：

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

Compact Review Mode 正式審查模板：
使用者要求正式審查報告時，必須保留以下欄位；無內容時填 `None`。

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

Large Codebase Review Mode 模板：
必須保留 `Review Scope`、`Current Batch`、`Review ledger`、`Batch summary`、依嚴重度分類的 findings、`Progress`、`Open questions`、`Residual risks` 與 `Continuation prompt`。
`High priority findings` 只列 Critical / Major 摘要或 finding 編號；完整內容放在 `Detailed findings`，避免重複。

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

## 產碼契約

- 產生或修改 Java 程式碼時，必須主動套用本地規則。
- 不得引入明顯違反命名、常數、布林欄位或結構規則的寫法。
- 若使用者明確要求偏離規則，必須指出偏離項目與理由。
- 若規則檔無法讀取，不得宣稱產出的程式碼符合本地 Java 規範。

## 適用範圍

- 預設適用於 production Java、core logic，以及一致性要求高的審查或產碼情境。
- 只有在使用者明確要求，或目標明確屬於一次性 script、POC、教學範例時，才可放寬規則。

## 參考文件

- 完整規則：`references/java-rules.md`
