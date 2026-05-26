# Skill 驗證腳本說明

本目錄提供 `java-code-review` skill 的驗證與 benchmark 腳本，目標是把 skill 規格檢查、單檔規則驗證、diff/PR 範圍驗證，以及 large-codebase workflow 驗證整理成可重複執行、可審計的流程。

注意：

- `skill_validation/` 是測試與 benchmark harness，不是 skill runtime 規格來源。
- `SKILL.md`、`references/java-rules.md`、`references/report-templates.md`、`references/review-workflow.md` 才是 skill 本體應遵循的來源。
- 調整 benchmark 時，不要把 parser、golden prompt 或單次測試需求反向寫回 `SKILL.md`。

## 使用套件

僅使用 Python 標準函式庫。

## 目錄結構

```text
skill_validation/
├─ README.md
├─ validate_skill.py
├─ run_golden_tests.py
├─ run_diff_golden_tests.py
├─ run_large_codebase_benchmarks.py
├─ README_golden.md
├─ README_diff_golden.md
├─ README_large_benchmark.md
└─ results/
   ├─ spec_validation/
   ├─ golden_tests/
   ├─ diff_golden_tests/
   └─ large_codebase_benchmarks/
```

## 本機重跑

```bash
python skill_validation/validate_skill.py --skill-root . --output-dir skill_validation/results/spec_validation --validation-mode auto
```

若要執行 benchmark：

```bash
python skill_validation/run_golden_tests.py --skill-root . --output-dir skill_validation/results/golden_tests --validation-mode auto
python skill_validation/run_diff_golden_tests.py --skill-root . --output-dir skill_validation/results/diff_golden_tests --validation-mode auto
python skill_validation/run_large_codebase_benchmarks.py --skill-root . --output-dir skill_validation/results/large_codebase_benchmarks --validation-mode auto
```

## 指定 skill 根目錄與輸出目錄

```bash
python skill_validation/validate_skill.py --skill-root C:\path\to\skill --output-dir C:\path\to\output --validation-mode auto
```

`--skill-root` 預設使用目前工作目錄；若目前目錄不是 skill 根目錄，腳本會依驗證 prompt 的規則嘗試 fallback。

## 啟用或停用 runtime validation

- `--validation-mode auto`：先偵測是否存在可審計的非互動 runtime；若找不到，降級為 `static_validation_only`。
- `--validation-mode runtime`：要求 runtime validation。若沒有可用 runtime，結果仍會誠實標記原因。
- `--validation-mode static`：只做規格、requirements、cases 與 coverage 對應檢查。

若要啟用 runtime validation，請設定環境變數 `CODEX_RUNTIME_COMMAND`，並提供可審計的命令模板。支援佔位符：

- `{prompt}`：直接代入 case prompt
- `{prompt_file}`：代入暫存 prompt 檔路徑
- `{skill_root}`：代入 skill 根目錄

範例：

```text
set CODEX_RUNTIME_COMMAND=codex exec --prompt-file {prompt_file}
```

## Gate A 到 Gate E 判斷邏輯

- Gate A 規格來源：檢查 `SKILL.md` 是否存在、至少一個 reference 是否存在，以及所有存在檔案是否可用 UTF-8 讀取。
- Gate B requirements 解析：檢查是否解析出 requirement，且每條 requirement 都有 `requirement_id`、`source_file`、`requirement_type`、`text`。
- Gate C case coverage：檢查 case 數量與分類下限，並驗證 trigger、不觸發條件、report template、review workflow、Java rules、缺檔或工具不可用、至少一條 MUST 與至少一條 MUST NOT 是否被 covered。
- Gate D validation mode：檢查 `runtime_validation` 與 `static_validation_only` 的輸出欄位是否誠實，避免把靜態檢查包裝成 runtime 驗證。
- Gate E 結果誠實：檢查 skip 不會算作 pass、summary 數字與 JSONL 是否一致，以及必要輸出路徑是否同時提供相對與絕對路徑。

## JSONL 欄位說明

`validation_results.jsonl` 每列代表一個 case，欄位如下：

- `case_id`：案例編號
- `category`：`positive|negative|edge|compliance`
- `prompt`：驗證 prompt
- `expected_behavior`：預期 skill 行為
- `actual_behavior`：本次驗證觀察到的行為
- `requirements_under_test`：本案例明確覆蓋的 requirement ids
- `source_files_under_test`：本案例對應的規格來源檔
- `command`、`working_directory`、`exit_code`、`stdout`、`stderr`：runtime validation 才會填值；static validation 必須為 `null`
- `passed`：本案例是否通過
- `validation_mode`：`runtime_validation` 或 `static_validation_only`
- `reason`：通過或失敗的判讀理由

## pass / fail / skip 判斷邏輯

- `pass`：案例對應的規格存在，且本次驗證模式下的檢查條件成立。
- `fail`：規格不存在、分類錯誤、coverage 不足，或 validation mode 輸出不誠實。
- `skip`：本腳本不使用 skip；`summary.results.skipped` 固定為 `0`，避免把 skip 美化成 pass。

## static validation 與 runtime validation 差異

- `static_validation_only`：只驗證規格來源、requirements 解析、case 設計與 coverage 映射，不代表 skill 已被實際執行。
- `runtime_validation`：代表腳本真的呼叫外部 runtime 執行 case prompt，並記錄命令、工作目錄、exit code、stdout、stderr。

## 如何解讀 requirements coverage

- `covered`：只有被 case 明確列在 `requirements_under_test`，且該 case 通過時，才會算 covered。
- `uncovered`：沒有任何通過 case 明確覆蓋的 requirement。
- `coverage_ratio`：`covered_requirements / total_requirements`。

`uncovered` 不代表規格錯誤，只代表目前案例沒有覆蓋到。

## 常見失敗原因與排查方式

- `SKILL.md` 或 reference 檔缺失：確認 skill 根目錄是否正確，且檔案存在。
- UTF-8 讀取失敗：確認檔案實際編碼為 UTF-8，或至少能以 UTF-8 正確讀取。
- requirements 過少：檢查規格內容是否缺少明確條列、關鍵字或結構。
- Gate C 失敗：檢查 case 是否少於 10 個、分類不足，或少了 trigger / workflow / report template / MUST / MUST NOT 等覆蓋。
- runtime validation 未啟用：確認是否設定 `CODEX_RUNTIME_COMMAND`，且命令支援非互動執行。
- summary 與 JSONL 不一致：重新執行腳本，避免人工修改結果檔。

## 建議測試分層

若目標是拿這個 skill 去 review 大專案，建議固定維持以下三層 benchmark：

1. `Single file golden test`
   - 驗證 rule 命中、嚴重度與中文表格 finding 是否合理。
2. `Diff / PR golden test`
   - 驗證只評論變更範圍，不混入未變更檔案。
3. `Large codebase workflow benchmark`
   - 驗證 inventory、批次審查、台帳、進度揭露與續跑提示。

這三層 benchmark 的輸出要求可以協助你檢查 skill 是否退化，但不應成為 `SKILL.md` 的唯一設計來源，更不應把 parser 細節直接寫回 runtime skill。

## 建議結果解讀方式

benchmark 結果建議拆成三組訊號，不要只看單一總 pass：

- `quality`
  - 有沒有抓到應抓的高風險問題，且沒有明顯 must-not finding。
- `scope`
  - 是否只評論應審查的範圍；diff case 代表不越界，大型專案 case 代表有清楚交代審查範圍。
- `format / workflow`
  - 單檔與 diff case 主要看中文表格與必要段落是否穩定；large-codebase case 主要看 inventory、batch、ledger、progress、continuation。
