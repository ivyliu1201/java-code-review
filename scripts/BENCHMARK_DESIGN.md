# Benchmark 設計總覽

本文件定義 `java-code-review` skill 的 benchmark 分層、案例設計原則，以及 quality / scope / workflow 的判讀方式。

目標不是讓 skill 背死固定輸出，而是驗證它是否真的適合拿去 review 大專案 Java backend。

## 設計目標

1. 驗證高風險 finding 是否穩定命中。
2. 驗證 diff / PR review 是否只評論變更範圍。
3. 驗證 large-codebase review 是否具備 inventory、batch、ledger、progress 與 continuation 能力。
4. 讓 benchmark 失敗時，可以快速分辨是 quality、scope，還是 workflow / format 問題。

## 非目標

- 不要求每次輸出都使用完全相同 wording。
- 不要求 parser 反向定義 `SKILL.md`。
- 不把所有架構原則都硬轉成 Must finding。
- 不把「缺測試」當成所有 PR 的第一優先 finding。

## 訊號分帳

| signal | 定義 | 典型失敗例子 |
|---|---|---|
| `quality` | 是否抓到應抓的高風險問題，且沒有明顯 must-not finding | 漏掉 `@Transactional` 內外部呼叫、漏掉敏感資料外洩 |
| `scope` | 是否只評論應審查範圍，或是否誠實揭露尚未審完的範圍 | diff review 扯到未變更檔案；大專案 review 沒交代未審查檔 |
| `workflow / format` | 是否有穩定的中文表格 finding 與必要 workflow 訊號 | 缺 `問題清單` 表格；large mode 沒有 `審查台帳` |

## 執行順序

建議固定依下列順序跑：

1. `spec validation`
   - 確認 skill runtime 與 references 可讀、可解析。
2. `single-file benchmark`
   - 先驗證 rule 命中。
3. `diff / PR benchmark`
   - 再驗證 scope 控制。
4. `large-codebase benchmark`
   - 最後驗證專案級 workflow。

若第 1 或第 2 層失敗，不建議直接拿第 3 層結果判斷 skill 是否能 review 大專案。

## Single-file Benchmark 設計

用途：驗證單一規則命中、嚴重度排序、中文表格 finding。

| case id | 核心規則 | 主要訊號 | 說明 |
|---|---|---|---|
| `sf-security-masking-01` | `H-2` | `quality` | 回傳或記錄完整敏感資料 |
| `sf-null-safe-equals-01` | `B-1` | `quality` | `nullable.equals(constant)` 型 NPE 風險 |
| `sf-transaction-boundary-01` | `L-1` / `J-7` | `quality` | 交易內直接呼叫外部支付或通知 |
| `sf-idempotency-01` | `J-6` | `quality` | 不可重複操作缺少冪等設計 |
| `sf-state-transition-01` | `J-1` | `quality` | request 狀態直接覆蓋 DB 狀態 |
| `sf-dto-entity-boundary-01` | `L-3` | `quality` | Controller 直接收/回 Entity |
| `sf-time-boundary-01` | `J-10` | `quality` | 直接用本機 `now()` 且邊界不清 |
| `sf-cache-sensitive-data-01` | `M-4` | `quality` | cache 寫入完整 token / 卡號 / 個資 |

Single-file 層的最低目標：

- `quality_pass` 應是主要判斷依據。
- `scope_pass` 固定為 `true`，只為了與其他層對齊欄位。
- `format_pass` 失敗不代表 skill 品質失敗，但代表正式輸出不夠穩。

## Diff / PR Benchmark 設計

用途：驗證只評論變更範圍、保留中文表格、避免把 distractor 檔案拉進來。

| case id | 核心規則 | 主要訊號 | 說明 |
|---|---|---|---|
| `diff-security-scope-01` | `H-2` | `scope` | 變更檔有敏感資料問題，未變更檔也放高風險 distractor |
| `diff-null-safety-01` | `B-1` | `quality` | 單行 diff 引入 NPE 風險 |
| `diff-transaction-01` | `L-1` / `J-7` | `quality` | 小 diff 讓交易邊界出問題 |
| `diff-maintainability-01` | `L-3` | `quality` | 變更讓 DTO / Entity 邊界破壞 |
| `diff-cache-scope-01` | `M-1` / `M-4` | `scope` | 只有改 cache key/value 的一小段，不應發散評論整個 cache layer |
| `diff-test-only-change-01` | `K-1` / `K-2` | `scope` | 只改測試或註解時，不應編造 production finding |
| `diff-multi-file-order-01` | `J-16` | `quality` | 跨兩個 changed files 的一致性問題 |
| `diff-unchanged-hotspot-01` | none | `scope` | 未變更檔案故意放更嚴重問題，驗證 skill 不越界 |

Diff 層的最低目標：

- `quality_pass=true` 但 `scope_pass=false` 時，表示 skill 看得懂問題，但還不適合直接做 PR reviewer。
- `scope_pass=true` 但 `quality_pass=false` 時，表示 skill 沒亂評論，但找問題能力不足。

## Large-codebase Benchmark 設計

用途：驗證大型專案審查 workflow，而不是單次輸出漂亮不漂亮。

| case id | 核心訊號 | 主要訊號 | 說明 |
|---|---|---|---|
| `lg-inventory-honesty-01` | inventory | `scope` | 超過 10 個 Java 檔，必須先盤點，不可假裝全審完 |
| `lg-batch-planning-01` | batching | `workflow` | 檔案數足以強迫分批 |
| `lg-ledger-progress-01` | ledger / progress | `workflow` | 要留下已審 / 待審台帳 |
| `lg-hotspot-priority-01` | review priority | `quality` | 同時存在資安、交易、命名問題，應優先報高風險 |
| `lg-cross-module-risk-01` | cross-module linkage | `quality` | 需要從 controller/service/cache/async 多檔串起風險 |
| `lg-pending-disclosure-01` | completion honesty | `scope` | 尚未審完時，明確揭露 pending |
| `lg-continuation-prompt-01` | continuation prompt | `workflow` | 未完成時提供下一輪續跑提示 |
| `lg-exclusion-discipline-01` | exclusions | `scope` | 測資含非 Java 檔、generated 檔，需明確排除並說明 |

Large-codebase 層的最低目標：

- `quality_pass` 代表至少抓到專案中刻意放入的高風險檔。
- `scope_pass` 代表有交代實際審查範圍與未完成範圍。
- `workflow_pass` 代表 inventory、batch、ledger、progress、continuation 足夠完整。

## Case 設計原則

1. 每個 case 只驗一到兩個核心目標。
2. 必須保留 `must_not_findings` 或 `scope guard`，避免 skill 靠大量泛論碰巧命中。
3. high-risk case 必須有明確 evidence，避免 matcher 只能靠關鍵字猜。
4. diff case 必須放 distractor 檔，否則測不到 scope。
5. large-codebase case 必須有足夠檔案數，否則測不到 batching。
6. 若規則依賴上下文，fixture 要補最小 stub，避免 skill 因找不到檔案而發散。

## 建議維護方式

| 類型 | 什麼時候改 | 原則 |
|---|---|---|
| `SKILL.md` | runtime 行為真的要變時 | 不因單次 benchmark fail 而改 |
| `java-rules.md` | 規則意圖真的要變時 | 先改規則，再補 benchmark |
| benchmark catalog | 要新增案例或補 coverage 時 | 只增不減，除非 case 設計錯誤 |
| matcher / parser | 明顯誤判時 | 修 parser，不要把 skill runtime 一起扭曲 |
