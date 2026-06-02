# Diff / PR Golden Test 驗證說明

本目錄提供 `java-code-review` skill 的 `Diff / PR golden test` 驗證腳本，用來檢查 skill 在 git diff / PR 場景下，是否能只評論變更範圍內的 Java 問題，而不把未變更檔案的既有問題混進本次 review。

## 本機重跑

```bash
python skill_validation/run_diff_golden_tests.py --skill-root . --output-dir skill_validation/results/diff_golden_tests --validation-mode auto
```

若只想重跑特定 diff case，可重複帶入 `--case-id`：

```bash
python skill_validation/run_diff_golden_tests.py --skill-root . --output-dir skill_validation/results/diff_golden_tests --validation-mode auto --case-id test-only-change-diff-01 --case-id multi-file-order-diff-01
```

若要啟用 runtime validation，請設定 `CODEX_RUNTIME_COMMAND`，例如：

```text
set CODEX_RUNTIME_COMMAND=codex.cmd exec -C {skill_root} --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox {prompt}
```

## 測試重點

每個 diff case 都會：

1. 建立一個最小 git repo
2. commit base snapshot
3. 依案例需要修改一個或多個 changed Java files，留下未提交 diff
4. 放入至少一個未變更的 distractor Java 檔案
5. 驗證 runtime output 是否：
   - 命中 diff 內應抓的問題
   - 不評論未變更檔案
   - 仍保有正式中文 review 的可讀性，且 `問題清單` 優先使用表格

目前 diff case 除了一般單檔變更，還包含：

- `test-only-change-diff-01`
  - 驗證只改測試時，不要編造 production finding。
- `multi-file-order-diff-01`
  - 驗證跨兩個 changed files 的一致性風險是否能被合併判讀。

## 額外驗證欄位

相較於 single-file golden test，diff harness 另外檢查：

- `scope_violations`
  - finding 指向未變更檔案時記錄
- `unchanged_file_mentions`
  - 最終輸出直接點名未變更檔案時記錄

只要上述任一欄位非空，該 case 就算失敗。

另外，若 finding 語意已命中，但 rule id 沒有精確對齊，腳本會記錄為 `rule_id_alignment_issues`。這類問題應優先視為規則標註品質問題，不應和「根本沒抓到 diff 風險」混為一談。

## 建議結果解讀方式

diff benchmark 建議拆成三組訊號來看：

- `quality_pass`
  - 有沒有抓到應抓的 diff finding，且沒有 must-not finding。
- `scope_pass`
  - 有沒有評論到未變更檔案，或把 finding 指到 diff 範圍外。
- `format_pass`
  - 中文表格、必要 workflow 訊號是否穩定。

`overall_pass` 只有在三者都通過時才成立。若 `quality_pass=true` 但 `scope_pass=false`，表示 skill 看得懂問題，但還不夠適合直接拿去做 PR review。

## 適用範圍

這支腳本對應測試金字塔中的第 2 層：

1. `Single file golden test`
2. `Diff / PR golden test`
3. `Project / large codebase golden test`

如果要拿去 review 大型專案，建議把這支 diff benchmark 視為第 2 層，並搭配第 3 層的 `run_large_codebase_benchmarks.py` 一起維護。
