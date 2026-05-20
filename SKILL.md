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

## 審查原則

1. 先檢查 Java diff 或目標檔案內容。
2. 以本地規則文件為主進行違規檢查，不要只做通用 style review。
3. findings 依使用者影響與嚴重度排序，優先列正確性、production 風險、可維護性下降，再列一致性與命名問題。
4. 若輸入內容包含檔案路徑、diff line 或可定位行號，finding 必須附上檔案與行號。
5. 單一 finding 預設使用精簡格式，只保留標題、規則、檔案行號、影響與修正方向。
6. finding 必須有具體依據，不可只憑偏好硬列問題。
7. 缺少必要上下文時，不可把推測當成確定 finding；應改列為 `Open Questions` 或 `Residual Risks`。
8. 如果沒有發現問題，要明確寫出沒有 findings，並補充剩餘風險或測試缺口。

## 嚴重度

- `Critical`: 明確的正確性、安全性、資料損壞、交易流程錯誤，或高機率 production 事故風險。
- `Major`: 明確規則違反、邏輯脆弱、可維護性重大缺陷，或高風險但未必立即造成事故的問題。
- `Minor`: 一致性、命名、可讀性、結構細節等非關鍵問題。
- `Suggestions`: 非必要但合理的改善建議。

## 審查模式

- 使用 Compact Review Mode：Java 檔案數小於等於 5，且所有 diff 或檔案內容可在單次 context 中完整審查。
- 使用 Large Codebase Review Mode：超過 5 個 Java 檔、整個資料夾、staged changes、壓縮包、多檔混合來源，或任何無法一次完整審查的範圍。
- Large Codebase Review Mode 必須先建立 Java file inventory，固定排序，分批 review；除非使用者明確允許抽樣，否則不可抽樣、不可跳檔、不可只挑重點檔案看。
- 只有在 inventory 中每個 Java 檔都已完成 review，才可宣稱全部 review 完成。
- 需要詳細 batch、ledger、完成條件或 final summary 規則時，讀取 `references/review-workflow.md`。

## 回應契約

- 先列 findings，再列摘要或變更說明。
- 依 `Critical`、`Major`、`Minor`、`Suggestions` 分類輸出；沒有問題的嚴重度要標示 `None` 或等價說法。
- Compact Review Mode 至少要交代 review scope 與 reviewed files。
- Large Codebase Review Mode 必須交代 scope、inventory 摘要、review ledger、目前批次與整體進度。
- 如果尚未 review 完所有檔案，必須明確寫出未完成狀態，不可暗示全面完成。
- 若使用者指定輸出格式或只要求特定嚴重度，盡量配合；但不得違反 mode 必要資訊與未完成狀態揭露要求。
- 需要正式模板、finding 標題範例或 Large Codebase Review Mode 輸出格式時，讀取 `references/report-templates.md`。

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
- 大型程式碼審查流程：`references/review-workflow.md`
- 審查報告模板：`references/report-templates.md`
