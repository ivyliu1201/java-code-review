# Java 程式審查 Skill

這是一個給 Codex 使用的 Java 程式審查 skill。它會依照本地 Java 規範進行 code review、命名與常數檢查、重構建議，以及正式 production Java 程式碼產生。

## 功能

- 依本地規則審查 Java 程式碼，不只做一般 style review。
- 檢查命名、常數、布林命名、magic value、結構一致性等規則。
- 支援小範圍 review 與大型 codebase 分批 review。
- 在產生或修改 Java 程式碼時，主動套用本地 Java 規範。
- 預設以繁體中文輸出審查報告。

## 專案結構

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
└── references/
    └── java-rules.md
```

- `SKILL.md`：skill 的主要行為規格與回應模板。
- `agents/openai.yaml`：OpenAI agent 顯示名稱、簡短描述與預設 prompt。
- `references/java-rules.md`：完整 Java 本地規則，審查與產碼前必須以 UTF-8 讀取。

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

輸出會包含：

- Review scope
- Reviewed files
- 依嚴重度分類的 findings
- Open questions
- Residual risks

### Large Codebase Review Mode

適用於超過 5 個 Java 檔、整個資料夾、staged changes、壓縮包、多檔混合來源，或任何無法一次完整審查的範圍。

此模式會先建立 Java file inventory，接著分批審查。除非使用者明確允許抽樣，否則不可跳檔或只挑重點檔案。

輸出會包含：

- Review scope
- Current batch
- Review ledger
- Batch summary
- High priority findings
- Detailed findings
- Progress
- Continuation prompt

## 嚴重度

- `Critical`：明確的正確性、安全性、資料損壞、交易流程錯誤，或高機率 production 事故風險。
- `Major`：明確規則違反、邏輯脆弱、可維護性重大缺陷，或高風險但未必立即造成事故的問題。
- `Minor`：一致性、命名、可讀性、結構細節等非關鍵問題。
- `Suggestions`：非必要但合理的改善建議。

## 規則來源

完整規則位於：

```text
references/java-rules.md
```

這個檔案是最高優先規則來源。若本地規則與通用 Java 慣例或 framework 慣例衝突，應優先揭露衝突點，並在放寬規則前說明取捨理由。

## 注意事項

- 審查、產碼或重構 Java 程式碼前，必須以 UTF-8 讀取 `references/java-rules.md`。
- 如果終端顯示亂碼，優先視為顯示編碼問題，不要直接改寫規則檔。
- 預設只做 review，不修改程式碼；只有使用者明確要求修改時，才實作修正。
- 若規則檔無法讀取，不得宣稱結果符合本地 Java 規範。

