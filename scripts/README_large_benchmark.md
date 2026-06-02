# Large Codebase Benchmark 驗證說明

本目錄提供 `java-code-review` skill 的 large-codebase workflow benchmark，用來驗證 skill 在檔案數較多、無法一次完整審查的情境下，是否真的啟用大型專案審查流程，而不是只輸出一份看似完整的短報告。

## 本機重跑

```bash
python scripts/run_large_codebase_benchmarks.py --skill-root . --output-dir scripts/results/large_codebase_benchmarks --validation-mode auto
```

若要啟用 runtime validation，請設定 `CODEX_RUNTIME_COMMAND`，例如：

```text
set CODEX_RUNTIME_COMMAND=codex.cmd exec -C {skill_root} --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox {prompt}
```

## 測試重點

這支腳本主要檢查第 3 層能力：

1. `inventory`
   - 是否先盤點 Java 檔案範圍，而不是直接假設整包都已 review 完。
2. `batching`
   - 是否明確交代目前批次，而不是把多檔大型審查壓成單次結論。
3. `review ledger`
   - 是否保留已審查 / 待審查的台帳資訊。
4. `progress honesty`
   - 如果仍有 pending，不可暗示整體 review 已完成。
5. `continuation prompt`
   - 未完成時是否提供可續跑的提示。

## 與前兩層 benchmark 的分工

1. `run_golden_tests.py`
   - 驗證單一規則命中與基本中文表格輸出。
2. `run_diff_golden_tests.py`
   - 驗證只評論變更範圍，不混入未變更檔案。
3. `run_large_codebase_benchmarks.py`
   - 驗證大型專案審查 workflow、進度誠實度與續跑能力。

這三層應分開維護，不要把 large-codebase workflow 的細節反向寫回 `SKILL.md` 當成每次 review 都必須硬符合的 parser 契約。

## 結果解讀

- `workflow_checks`
  - 各 workflow 訊號是否存在，例如 `審查範圍`、`目前批次`、`審查台帳`、`進度`。
- `workflow_issues`
  - 缺少的 workflow 訊號清單。
- `pending_markers_detected`
  - 是否明確揭露仍有待審查檔案。
- `finding_signal_pass`
  - 是否至少有具體 finding 指向 benchmark 中刻意放入的問題檔案。
- `quality_pass`
  - 是否至少抓到應有的問題訊號。
- `scope_pass`
  - 是否有清楚交代審查範圍。
- `overall_pass`
  - quality、scope、workflow 都通過時才算通過。

## 設計原則

- 這支 benchmark 的目標是驗證「能不能審查大專案」，不是要求 skill 背死單一輸出 wording。
- 正式輸出仍預設使用繁體中文，且 `問題清單` 優先使用中文表格。
- 若 workflow 有達成，但欄位名稱存在小幅同義變體，應優先視為 harness 調整議題，而不是回頭污染 skill 本體。
