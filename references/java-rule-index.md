# Java 規則索引

此檔只用於快速定位 `references/java-rules.md`。正式規則、例外與範例一律以 `references/java-rules.md` 原文為準，不得只憑本索引下結論。

## 使用方式

- 先依問題類型在本索引找到章節與關鍵字。
- 再以 UTF-8 讀取 `references/java-rules.md` 的對應章節。
- Review finding 的 `Rule` 欄位使用 `java-rules.md` 的原始規則編號，例如 `A-5`、`D-1`、`K-1`。

## 章節導覽

- `0`: Code Review Operating Rules。優先檢查安全性、業務正確性、交易一致性、資料庫、例外、可維護性，再檢查命名與格式。
- `A`: Naming & Constants。命名、常數、布林欄位、package、magic value、enum。
- `B`: OOP & 基礎語言使用。equals、包裝型別比較、hashCode、方法責任。
- `C`: Collections & Generics。集合修改、Arrays.asList、toArray、raw type。
- `D`: Concurrency。thread pool、ThreadLocal、共享可變狀態、new Thread。
- `E`: Exceptions & Resource Management。例外處理、資源關閉、日誌與可追蹤性。
- `F`: Logs。SLF4J、例外日誌、業務上下文、高頻路徑日誌成本。
- `G`: SQL / ORM / Database。唯一索引、JOIN、分頁查詢、參數綁定、全欄位更新、明確映射。
- `H`: Security。授權檢查、敏感資料脫敏、HTML escaping、CSRF、不可只依賴前端限制。
- `I`: Other Basic Rules。正則預編譯、Random API、機械一致風格、陣列宣告、設計模式與 implementation 命名。
- `J`: Business Logic & Domain Safety。狀態流轉、金額與庫存、冪等、交易一致性、補償、對帳與業務不變式。
- `K`: Tests & Review Coverage。核心邏輯測試、異常與邊界、外部系統測試。
- `L`: Spring / Framework / Transaction Usage。交易邊界、Controller、DTO/Entity、singleton 狀態、自動綁定。
- `M`: Cache & Distributed Safety。cache key、一致性、分散式鎖、敏感資料。

## 常用 grep 關鍵字

- 命名與常數：`A-1|A-5|A-7|A-10`
- equals / 包裝型別：`B-1|B-2|B-3`
- 集合與泛型：`C-1|C-2|C-4`
- 併發：`D-1|D-2|D-3|D-4`
- 例外與資源：`E-1|E-2`
- 日誌：`F-1|F-2|F-3`
- SQL / ORM / DB：`G-1|G-5|G-7|G-8`
- 安全：`H-1|H-2|H-3|H-4|H-5`
- 業務安全：`J-1|J-3|J-6|J-7|J-16|J-17`
- 測試覆蓋：`K-1|K-2|K-3|K-4`
- Spring 交易與邊界：`L-1|L-2|L-3|L-4|L-5`
- Cache / 分散式安全：`M-1|M-2|M-3|M-4`
