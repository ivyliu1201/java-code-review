# Golden Test 驗證說明

本目錄提供 `java-code-review` skill 的 single-file golden test 驗證腳本，用來檢查 Java code review skill 在單檔或小範圍情境下，是否能穩定命中核心規則，並輸出可讀、可審計的中文 findings。

## 使用套件

僅使用 Python 標準函式庫。

## 目錄結構

```text
scripts/
├─ README_golden.md
├─ run_golden_tests.py
├─ golden_cases/
│  └─ *.java                  # 由腳本每次重建
└─ results/
   └─ golden_tests/
      ├─ golden_results.jsonl
      ├─ golden_summary.json
      └─ spec_source_manifest.json
```

## 本機重跑

```bash
python scripts/run_golden_tests.py --skill-root . --output-dir scripts/results/golden_tests --validation-mode auto
```

若要跑 holdout 驗收集，改用：

```bash
python scripts/run_golden_tests.py --skill-root . --output-dir scripts/results/holdout_tests --case-set holdout --validation-mode auto
```

## 指定 skill 根目錄與輸出目錄

```bash
python scripts/run_golden_tests.py --skill-root C:\path\to\skill --output-dir C:\path\to\output --validation-mode auto
```

`--skill-root` 預設使用目前工作目錄；若目前目錄不是 skill 根目錄，腳本會依 prompt 規則 fallback。

## Case Set

- `--case-set baseline`：預設值，用於日常調整與回歸
- `--case-set holdout`：不參與調參的驗收案例，適合做最終品質檢查
- `--case-set all`：一次執行 baseline + holdout，適合大改版後做完整盤點

建議做法：

1. 平常只跑 `baseline`
2. skill 或模板定稿前再跑 `holdout`
3. 只有在大幅改動 skill、matcher 或流程時才跑 `all`

## 啟用或停用 runtime validation

- `--validation-mode auto`：先偵測可審計的非互動 runtime；找不到時降級為 `static_validation_only`
- `--validation-mode runtime`：要求 runtime validation；若不可用，summary 會誠實標記原因
- `--validation-mode static`：只驗證 golden case 結構、rule 對應與比對邏輯存在

若要啟用 runtime validation，請設定環境變數 `CODEX_RUNTIME_COMMAND`。支援以下佔位符：

- `{prompt}`：直接插入 prompt 文字
- `{prompt_file}`：插入 UTF-8 prompt 檔路徑
- `{skill_root}`：插入 skill 根目錄

範例：

```text
set CODEX_RUNTIME_COMMAND=codex exec --prompt-file {prompt_file}
```

## Gate A 到 Gate E 判斷邏輯

- Gate A 規格來源：檢查 `SKILL.md`、`references/java-rules.md` 是否存在，其他 reference 缺失是否有標記 notes，以及所有存在檔案是否可用 UTF-8 讀取
- Gate B golden case 設計：檢查 case 數量、必要類別、expected finding 欄位、must-not finding、rule id 對應與「測資由腳本產生」條件
- Gate C runtime 誠實：檢查 `runtime_validation` 是否真的有 command / working directory / exit code / stdout / stderr；檢查 static mode 沒有冒充已驗證準確度
- Gate D 比對品質：runtime mode 會以 issue / evidence / recommendation / severity 的語意對應為主；若 rule id 未完全對齊，會另外記錄為 `rule_id_alignment_issues`
- Gate E 結果誠實：檢查 summary 與 JSONL 一致、skip 不算 pass，以及輸出路徑同時含相對與絕對路徑

## 如何新增 golden case

在 `run_golden_tests.py` 的 `build_baseline_case_specs()` 或 `build_holdout_case_specs()` 裡新增 case，並遵守：

1. 每個 case 只聚焦一類核心問題
2. Java 測資直接寫在 `java_source`
3. `expected_findings` 至少一筆，且每筆都要有 `rule_id`、`severity`、`expected_issue`、`expected_evidence`、`expected_recommendation`
4. `must_not_findings` 至少一筆
5. `source_rules_under_test` 要對應 `references/java-rules.md` 的正式 rule id

## `golden_results.jsonl` 欄位說明

- `golden_case_id`：golden case 編號
- `category`：案例類別
- `java_file`：由腳本產生的 Java 測資相對路徑
- `expected_findings`：預期命中的 finding 規格
- `actual_findings`：runtime 輸出解析結果
- `matched_findings`：命中 expected finding 的 actual findings
- `missed_findings`：預期但未命中的 finding
- `unexpected_findings`：無法對應 expected finding 的 actual findings
- `rule_id_alignment_issues`：finding 語意命中，但 rule id 沒有精確對齊的項目
- `must_not_violations`：命中不應出現 finding 的項目
- `quality_pass`：核心 finding 品質是否通過
- `scope_pass`：single-file benchmark 固定為 `true`，保留欄位是為了和 diff / large benchmark 對齊
- `template_compliance`：是否符合 `report-templates.md` 必要欄位
- `workflow_compliance`：是否符合 `review-workflow.md` 必要流程資訊
- `format_pass`：表格與 workflow 訊號是否整體通過
- `overall_pass`：quality 與 format 訊號都通過時才算通過
- `precision_estimate`：`matched_findings / actual_findings`
- `recall_estimate`：`matched_findings / expected_findings`
- `command`、`working_directory`、`exit_code`、`stdout`、`stderr`：只有 runtime mode 會填值
- `passed`：runtime mode 代表 case 真正通過；static mode 只代表 case 結構檢查通過
- `validation_mode`：`runtime_validation` 或 `static_validation_only`
- `reason`：通過或失敗原因

## precision / recall 判斷方式

- precision：actual findings 中有多少是命中 expected findings
- recall：expected findings 中有多少被 actual findings 命中
- runtime mode 不可只靠文字相似度；必須同時檢查 issue、evidence、recommendation，且 high / critical 不可被低估
- static mode 的 precision / recall 固定為 `0.0`，不得宣稱代表實際 review 準確度

## 建議看法

single-file benchmark 最重要的是 `quality_pass`。若 `overall_pass=false` 但 `quality_pass=true`，通常代表 skill 有抓到問題，只是中文表格或 workflow 訊號還不夠穩定。

## pass / fail / skip 判斷邏輯

- `pass`：
  - runtime mode：無 missed findings、無 must-not violations、template/workflow 合規
  - static mode：case 結構、rule 對應與比對邏輯存在
- `fail`：缺少必要欄位、rule 對應錯誤、runtime 輸出不合規，或結果不誠實
- `skip`：本腳本不使用 skip；`skipped_golden_cases` 固定為 `0`

## static validation 與 runtime validation 差異

- `runtime_validation`：代表腳本真的逐一執行 golden case review prompt，並根據輸出內容做 finding 比對
- `static_validation_only`：只代表 golden case 結構、規格來源、rule 對應與比對邏輯檢查通過，不代表實際 review 準確度已驗證

## 常見失敗原因與排查方式

- 找不到 `references/java-rules.md`：先修正 skill 根目錄或補回正式規則檔
- golden case 類別不足：補齊 security、null_safety、transaction/resource_handling、performance、maintainability
- expected finding 沒有對到本地 rule id：修正 `rule_id` 或調整 case 設計
- runtime validation 沒啟用：確認 `CODEX_RUNTIME_COMMAND` 是否存在且可非互動執行
- template/workflow 不合規：檢查 skill 輸出是否仍具有中文表格 finding 與必要 workflow 訊號；若只是小幅欄位別名差異，優先視為 harness 調整議題

## Benchmark 凍結規則

當 golden harness 完成結構性修正後，建議將目前這套 benchmark 視為 `v1`，後續遵守以下原則：

1. 只允許修正 harness bug，例如編碼、case 隔離、解析器明顯誤判
2. 不因單次 runtime 輸出不理想而回頭放寬 matcher
3. 不刪除現有難 case，只能新增 case
4. skill 調整與 benchmark 調整分開進行；調 skill 時，優先重跑同一版 benchmark
5. 最好另外維護一組不參與調參的 holdout cases，作為最終驗收

## 建議測試分層

若最終目標是 review 大型專案，建議不要只停在 single-file benchmark：

1. `Single file golden test`
   - 驗證單一規則命中、嚴重度與中文表格 finding
2. `Diff / PR golden test`
   - 驗證只評論變更範圍、檔案定位、diff line 與 scope 控制
3. `Project / large codebase golden test`
   - 驗證 inventory、批次審查、審查台帳、進度與續跑提示

目前這支 `run_golden_tests.py` 屬於第 1 層；如果要拿去 review 公司大型專案，應搭配第 2 層與第 3 層一起看，而不是拿單檔 golden 結果直接代表大型專案能力。
