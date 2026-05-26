# Java 程式審查 Skill

這是一個給 Codex 使用的 Java 程式審查 skill。它會依照本地 Java 規範進行 code review、命名與常數檢查、重構建議，以及正式 production Java 程式碼產生。

## 目前版本重點

- `SKILL.md` 保留核心入口規則，讓 Codex 觸發 skill 後快速掌握必做事項。
- 完整 Java 規範放在 `references/java-rules.md`，審查、產碼或重構前必須以 UTF-8 讀取。
- `references/java-rule-index.md` 提供大型規則檔的快速索引，但不取代正式規則原文。
- 大型 codebase review 的 inventory、batch、ledger 與完成條件放在 `references/review-workflow.md`。
- Review 報告模板與 finding 標題範例放在 `references/report-templates.md`。
- 預設以繁體中文輸出審查報告，正式報告優先使用中文表格。

## 功能

- 依本地 Java 規範審查程式碼，不只做一般 style review。
- 檢查命名、常數、布林欄位、magic value、結構一致性等規則。
- 支援小範圍 Compact Review Mode。
- 支援大型範圍 Large Codebase Review Mode，要求先建立 Java file inventory 並分批審查。
- 產生或修改 Java 程式碼時，主動套用本地規則。
- 明確禁止抽樣、跳檔或在未完成時宣稱全部 review 完成。

## 專案結構

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
├── skill_validation/
│   ├── validate_skill.py
│   ├── run_golden_tests.py
│   ├── run_diff_golden_tests.py
│   └── README*.md
└── references/
    ├── java-rules.md
    ├── java-rule-index.md
    ├── report-templates.md
    └── review-workflow.md
```

- `SKILL.md`：skill 入口規則、觸發後的必做要求、審查原則與 reference 導覽。
- `agents/openai.yaml`：OpenAI agent 顯示名稱、簡短描述與預設 prompt。
- `references/java-rules.md`：完整 Java 本地規則，審查與產碼前必讀。
- `references/java-rule-index.md`：大型規則檔快速索引，方便先定位再回原文確認。
- `references/review-workflow.md`：大型審查流程、批次規則、完成條件與 final summary 要求。
- `references/report-templates.md`：一般 review、Compact 正式 review、Large Codebase Review Mode 的輸出模板。
- `skill_validation/`：測試與 benchmark 腳本。這些腳本是驗證工具，不是 skill runtime 規格來源。

## 安裝

將此資料夾放到 Codex skills 目錄下：

```text
%USERPROFILE%\.codex\skills\java-code-review
```

放置後，Codex 會在可用 skills 中看到 `java-code-review`。

## 使用方式

在對話中明確要求使用此 skill，例如：

```text
Use $java-code-review to review this Java change against the local Java rules.
```

或以繁體中文描述需求：

```text
請用 java-code-review 依本地 Java 規範審查這次修改。
```

## 審查模式

### Compact Review Mode

適用於 Java 檔案數小於等於 5，且所有 diff 或檔案內容可在單次 context 中完整審查的情境。

基本要求：

- 列出 review scope 與 reviewed files。
- 不可抽樣。
- 不可跳檔。
- 找不到問題時也要明確說明沒有 findings，並補充剩餘風險或測試缺口。

### Large Codebase Review Mode

適用於超過 5 個 Java 檔、整個資料夾、staged changes、壓縮包、多檔混合來源，或任何無法一次完整審查的範圍。

基本要求：

- 先建立 Java file inventory。
- 使用穩定排序，建議依路徑排序。
- 列出排除項目與理由。
- 建立批次計畫。
- 每批最多審查 10 個 Java 檔，複雜檔案應縮小批次。
- 只有 inventory 中每個 Java 檔都完成 review，才可宣稱全部完成。

## 嚴重度

- 中文正式報告預設使用 `嚴重`、`主要`、`次要`、`建議`。
- 使用者要求英文時，可改用 `Critical`、`Major`、`Minor`、`Suggestions`。

## 規則來源

完整規則位於：

```text
references/java-rules.md
```

這個檔案是最高優先規則來源。若本地規則與通用 Java 慣例或 framework 慣例衝突，應優先揭露衝突點，並在放寬規則前說明取捨理由。

## 驗證

可用官方 skill 驗證腳本檢查基本格式：

```powershell
$env:PYTHONUTF8='1'
python C:\Users\fanny\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\fanny\.codex\skills\java-code-review
```

預期輸出：

```text
Skill is valid!
```

若要保留腳本測試，建議把測試分成三層，並讓它們與 skill runtime 規格分離：

1. `Single-file rule benchmark`
   驗證單一規則是否能穩定命中。
2. `Diff / PR scope benchmark`
   驗證只評論變更範圍、避免把未變更檔案混進 findings。
3. `Large-codebase workflow benchmark`
   驗證 inventory、batch、ledger、進度與續跑提示。

測試腳本可以存在 `skill_validation/`，但不要再把 golden prompt 或 parser 契約直接寫回 `SKILL.md`。

## 注意事項

- 審查、產碼或重構 Java 程式碼前，必須以 UTF-8 讀取 `references/java-rules.md`。
- 如果終端顯示亂碼，優先視為顯示編碼問題，不要直接改寫規則檔。
- 預設只做 review，不修改程式碼；只有使用者明確要求修改時，才實作修正。
- 若規則檔無法讀取，不得宣稱結果符合本地 Java 規範。

