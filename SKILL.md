---
name: java-code-review
description: 當使用者要求依照本地 Java 規範進行 code review、命名/常數檢查、重構，或產生正式 production Java 程式碼時使用。套用規則前必須先以 UTF-8 讀取 references/java-rules.md。
---

# Java 程式審查

當使用者要求依照本地 Java 規範進行程式審查、產生程式碼或重構時，使用這個 skill。

## 必做規則

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
- `references/java-rule-index.md` 可作為大型規則檔的快速索引，但不取代 `references/java-rules.md` 原文。

## 審查原則

1. 先檢查 Java diff 或目標檔案內容。
2. 以本地規則文件為主進行違規檢查，不要只做通用 style review。
3. findings 依使用者影響與嚴重度排序，優先列正確性、production 風險、可維護性下降，再列一致性與命名問題。
4. 若輸入內容包含檔案路徑、diff line 或可定位行號，finding 必須附上檔案與行號。
5. 單一 finding 預設使用精簡格式，但正式報告中的主要問題清單至少要交代類型、信心、標題、檔案行號、證據、影響與修正方向。
6. finding 必須有具體依據，不可只憑偏好硬列問題。
7. 缺少必要上下文時，不可把推測當成確定 finding；應使用信心欄位區分 `已確認`、`高度可能`、`需確認`，並把未定事項移到開放問題或剩餘風險。
8. 如果沒有發現問題，要明確寫出沒有 findings，並補充剩餘風險或測試缺口。

## 嚴重度與輸出語言

- 預設以繁體中文輸出；使用者要求英文時，改用英文。
- 正式報告預設以中文表格呈現 findings。
- 嚴重度應與輸出語言一致，並保持由高到低的穩定排序。
- 中文使用 `嚴重`、`主要`、`次要`、`建議`。
- 英文可使用 `Critical`、`Major`、`Minor`、`Suggestions`。
- `java-rules.md` 標示為 `Must` 的規則，預設至少列為高風險層級；涉及安全、金額、資料一致性、交易、權限或 production 事故風險時，應提升到最高層級。
- `java-rules.md` 標示為 `Should` 的規則，預設列為次高或改善建議；若上下文顯示實際 production 風險，可提升嚴重度。

## 審查模式

- 使用 Compact Review Mode：Java 檔案數小於等於 5，且所有 diff 或檔案內容可在單次 context 中完整審查。
- 使用 Large Codebase Review Mode：超過 5 個 Java 檔、整個資料夾、staged changes、壓縮包、多檔混合來源，或任何無法一次完整審查的範圍。
- 啟用 Large Codebase Review Mode 時，必須讀取 `references/review-workflow.md`，並依 inventory、batch、ledger 與 completion rule 執行。

## 回應原則

- 先列 findings，再補審查範圍、進度、開放問題與剩餘風險。
- findings 應依嚴重度分類，並在可能時附 rule id、檔案、行號、證據、影響與修正方向。
- 正式報告與預設中文輸出時，`問題清單` 必須使用 Markdown 表格呈現。
- 正式報告與預設中文輸出時，Compact Review Mode 的 top-level 段落順序固定為：`問題清單`、`審查範圍`、`開放問題`、`剩餘風險`。
- `問題清單` 表格欄位固定為 `嚴重度 | 類型 | 信心 | 標題 | 檔案行號 | 證據 | 影響 | 修正方向`，其中 `檔案行號` 使用純文字 `relative/path/File.java:123`。
- 若需要保留精確 rule id，優先放在 `標題` 開頭，例如：`L-1 交易邊界不正確`。
- `類型` 只用可快速判斷風險來源的短標籤，例如：`錯誤`、`資安`、`個資`、`交易`、`資料一致性`、`業務邏輯`、`測試缺口`、`可維護性`。
- `類型` 每筆 finding 只選一個主類型，不要輸出複合值，例如 `交易 / 資料一致性`；也不要自創新標籤，例如 `對帳`。若風險本質是對帳、補償、跨表落庫、快取一致性或最終一致性，統一歸到 `資料一致性`。
- `信心` 只使用 `已確認`、`高度可能`、`需確認`。
- `證據` 應引用目前可見程式碼中的具體呼叫、欄位、條件或語句，不要只寫抽象判斷。
- `修正方向` 應控制在簡短、具體、可落地的 review 指引；不要提供完整程式碼、patch、教學文或大型重構方案。
- 不要退回舊六欄表 `嚴重度 | 規則 | 位置 | 問題 | 風險 | 建議`，也不要改用 `Findings`、`Open Questions`、`Change Summary` 等英文 section。
- Compact Review Mode 至少要交代 review scope 與 reviewed files，並在 `審查範圍` 中明確列出 `- 範圍: ...` 與 `- 已審查檔案: ...`。
- Large Codebase Review Mode 必須交代 scope、inventory 摘要、review ledger、目前批次與整體進度。
- 如果尚未 review 完所有檔案，必須明確寫出未完成狀態，不可暗示全面完成。
- 若使用者指定輸出格式或只要求特定嚴重度，盡量配合；但不得違反 mode 必要資訊與未完成狀態揭露要求。
- 需要正式模板、finding 標題範例或 Large Codebase Review Mode 輸出格式時，讀取 `references/report-templates.md`。

## Diff / PR 審查契約

- 使用者要求 review diff、PR、staged changes 或 git 變更時，預設只審查本次 diff 中有變更的 Java 檔案與變更行附近必要上下文。
- 不要把未變更檔案的既有問題混進本次 findings；若未變更檔案影響判斷，可在開放問題或剩餘風險中保守說明。

## 產碼契約

- 產生或修改 Java 程式碼時，必須主動套用本地規則。
- 不得引入明顯違反命名、常數、布林欄位或結構規則的寫法。
- 若使用者明確要求偏離規則，必須指出偏離項目與理由。
- 若規則檔無法讀取，不得宣稱產出的程式碼符合本地 Java 規範。

## 適用範圍

- 預設適用於 production Java、core logic，以及一致性要求高的審查或產碼情境。
- 只有在使用者明確要求，或目標明確屬於一次性 script、POC、教學範例時，才可放寬規則。

## 參考文件

- 完整 Java 規則：`references/java-rules.md`
- Java 規則索引：`references/java-rule-index.md`
- 大型程式碼審查流程：`references/review-workflow.md`
- 審查報告模板：`references/report-templates.md`
