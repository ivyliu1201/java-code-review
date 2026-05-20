# 審查流程

執行 `java-code-review` 的 Java 程式審查時使用此參考文件；特別是審查範圍超過少數檔案，或需要跨批次追蹤進度時。

## Compact Review Mode

當 Java 審查範圍小於等於 5 個 Java 檔，且所有相關 diff 或檔案內容可在單次回覆中完整審查時，使用 Compact Review Mode。

- 列出 review scope 與 reviewed files。
- 不可抽樣。
- 不可跳檔。
- 除非範圍內每個 Java 檔都已完成審查，否則不可宣稱完成。
- 如果內容過大，無法一次完整涵蓋，改用 Large Codebase Review Mode。

## Large Codebase Review Mode

當範圍超過 5 個 Java 檔、整個資料夾、staged changes、壓縮包、多檔混合輸入，或任何無法一次完整審查的範圍時，使用 Large Codebase Review Mode。

輸出 findings 前，先完成以下事項：

1. 建立 Java file inventory。
2. 使用穩定順序排序檔案，建議依 path ascending。
3. 列出排除檔案與排除理由。
4. 建立批次計畫。
5. 每批最多審查 10 個 Java 檔；若檔案較大或邏輯複雜，使用更小批次。

Inventory 至少包含：

- Review scope
- Java 檔案總數
- 完整 Java 檔案清單
- 排除項目與理由
- 批次計畫

## 批次規則

Large Codebase Review Mode 的每個批次都必須包含：

- 目前批次編號
- 本批已審查檔案
- Review ledger
- 依 `Critical`、`Major`、`Minor`、`Suggestions` 分類的 findings
- 進度與剩餘檔案
- Open questions
- Residual risks
- 未完成時的 continuation prompt

不可把多個批次混成一份界線不明的報告。如果單一批次報告太長，可拆成 `Part 1`、`Part 2` 等段落，但必須保留同一個批次編號。

## 完成條件

- 只要 inventory 中仍有任何檔案 pending，就不可宣稱 review 完成。
- 無法完成全部範圍時，只能停在批次邊界。
- 未完成時，列出已審查檔案、待審查檔案、目前批次、下一批起點與 continuation prompt。
- 輸出 final summary 前，確認 inventory 中每個項目都已標記為 `reviewed`、`pending` 或 `excluded`。
- 若仍有任何項目是 `pending`，輸出進度而不是 final summary。

## 最終摘要必備內容

只有在所有批次完成後，才可包含：

- Java 檔案總數
- 已審查 Java 檔案數
- `Critical`、`Major`、`Minor`、`Suggestions` 數量統計
- 最高風險檔案
- Top priority fixes
