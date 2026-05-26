# java-code-rules.md

> 目的：作為 `java-code-review` skill 在 Java code review、Java 程式碼產生與重構時的本地規則來源，要求 AI agent 在審查、產生或修改 production Java code 前，先理解並套用本文件。
>
> 原則：以下規則以可執行、低歧義、可驗證、可穩定套用為優先；若規則與一般 Java 慣例、框架預設或個人偏好衝突，應優先採用能降低安全性、資料正確性、交易一致性與 production 風險的寫法。
>
> 說明：
> - 本文件為 AI coding agent 在進行 Java code review、產生 Java 程式碼或重構 Java 程式碼前必須遵守的本地硬性規則。
> - 規則優先於個人偏好、框架預設行為、臨時寫法與單純追求簡潔的實作。
> - 若遇到規則衝突，以「避免風險 > 可讀性 > 簡潔性」為優先順序。
> - 本文件主要適用於正式業務程式碼（production / core logic）；一次性 migration、POC、教學範例除非有明確要求，否則可視情境放寬。

---
# 0 區：Code Review Operating Rules

> 目的：定義 AI 進行 Java code review 時的審查順序、嚴重度、輸出格式與判斷原則，避免只挑風格問題而漏掉真正的 production risk。

---

## 0-1 Review 優先順序

**規則**
- Code review 時應依下列順序找問題：
  1. 安全性、越權與敏感資料外洩。
  2. 業務正確性、狀態流轉與資料歸屬。
  3. 交易一致性、冪等、併發、重試與補償。
  4. 資料庫正確性、SQL 安全與效能風險。
  5. 例外處理、日誌、稽核與可觀測性。
  6. 可維護性、可測試性與架構邊界。
  7. 命名、格式與局部風格。
- 不得因為找到低風險命名或格式問題，就忽略高風險業務、交易、資安與資料一致性問題。

**原因**
- Code review 的首要目標是降低 production risk，而不是只追求程式碼外觀一致。

---

# A 區：Naming & Constants

## A-1 名稱不可以下劃線或 `$` 開頭或結尾

**規則**
- 不要產生以下劃線 `_` 或美元符號 `$` 作為開頭或結尾的類名、方法名、變數名、常數名。

**原因**
- 這類命名不符合規範，會降低一致性與可讀性。

**反例**
```java
String _name;
int id_;
String $token;
```

**正例**
```java
String name;
int userId;
String token;
```

---

## A-2 命名禁止使用中文、拼音或中英混寫

**規則**
- 類名、方法名、變數名、常數名、package 名一律使用可理解的英文。
- 不要使用中文。
- 不要使用拼音。
- 不要混用英文與拼音或英文與中文。

**原因**
- 可讀性差，跨團隊協作成本高，搜尋與維護困難。

**反例**
```java
int dingweizhi;
String mingCheng;
```

**正例**
```java
int offset;
String name;
```

---

## A-3 類名使用 UpperCamelCase，且以名詞為主

**規則**
- 類名採用 UpperCamelCase。
- 類名應該是可辨識的名詞。
- 可保留常見後綴，如 `DO`、`DTO`、`VO`、`DAO`。

**原因**
- 便於辨識角色與責任，保持專案結構一致。

**反例**
```java
public class userinfo {}
public class updateUser {}
```

**正例**
```java
public class UserInfo {}
public class UserProfileDTO {}
```

---

## A-4 方法、參數、成員變數、區域變數使用 lowerCamelCase

**規則**
- 方法名、方法參數、成員變數、區域變數一律使用 lowerCamelCase。

**原因**
- 這是 Java 主流慣例，可降低閱讀摩擦。

**反例**
```java
private String UserName;
public void GetUserInfo(String User_Id) {}
```

**正例**
```java
private String userName;
public void getUserInfo(String userId) {}
```

---

## A-5 常數使用全大寫與底線分隔

**規則**
- `static final` 常數名稱使用全大寫。
- 多個單字之間以底線分隔。
- 常數名要完整表意，不要過度縮寫。

**原因**
- 可快速識別常數，避免與一般變數混淆。

**反例**
```java
static final int timeoutms = 5000;
static final String key = "demo";
```

**正例**
```java
static final int TIMEOUT_MILLIS = 5000;
static final String DEMO_KEY = "demo";
```

---

## A-6 特殊類型名稱要反映角色

**規則**
- 抽象類以 `Abstract` 或 `Base` 開頭。
- 例外類以 `Exception` 結尾。
- 測試類以被測類名開頭，並以 `Test` 結尾。

**原因**
- 便於快速辨識類型用途，提升可搜尋性與維護性。

**反例**
```java
class UserError {}
class CommonProcessor {}
class LoginCase {}
```

**正例**
```java
class UserNotFoundException extends RuntimeException {}
abstract class AbstractProcessor {}
class LoginServiceTest {}
```

---

## A-7 布林欄位不要命名成 `isXxx`

**規則**
- 布林成員變數不要直接命名為 `isSuccess`、`isDeleted` 這種形式。
- 優先使用 `success`、`deleted`、`enabled` 等名稱。
- 本規則僅適用於欄位名稱（field），不限制 JavaBean getter 方法名稱（例如 `isEnabled()` 合法）。
- 若 framework 明確要求 `is_xxx` 對應 DB 欄位，應在 mapping 層處理，不影響 Java 欄位命名規則。

**原因**
- 某些 framework 在序列化、反射或屬性推導時，可能把 `isSuccess` 推導成 `success`，導致欄位解析或序列化錯誤。

**反例**
```java
private Boolean isSuccess;
```

**正例**
```java
private Boolean success;
```

---

## A-8 package 名稱全小寫，且保持簡單一致

**規則**
- package 名稱全部小寫。
- 每一層 package 優先使用單一英文單字。
- package 名採單數形式。
- 若既有專案已使用固定 package 命名慣例，應優先保持專案一致。

**原因**
- 可維持結構一致，避免大小寫與命名風格混亂。

**反例**
```java
package com.CompanyName.Users;
package com.demo.userProfiles;
```

**正例**
```java
package com.company.user;
package com.demo.profile;
```

---

## A-9 避免不常見或難懂的縮寫

**規則**
- 不要自行創造難懂縮寫。
- 優先使用完整、常見、容易理解的英文單字。
- 若縮寫不是 Java / JDK 標準用語（如 `id`、`url`、`http`）或業界高度通用縮寫（如 `biz`、`dto`、`vo`、`dao`），視為不建議使用。
- 若縮寫需要額外解釋，則不適合使用。

**原因**
- 降低理解成本，避免不同人對縮寫有不同解讀。

**反例**
```java
int condi;
String bizStsCd;
```

**正例**
```java
int condition;
String businessStatusCode;
```

---

## A-10 避免 magic value；固定值域優先考慮 enum

**規則**
- 不要直接把沒有語意的數字或字串散落在業務邏輯中。
- 若值域固定且具有明確狀態意義，優先使用 enum。

**原因**
- 可讀性更高，降低誤用與維護成本。

**反例**
```java
if (status == 1) {
    // active
}
```

**正例**
```java
if (status == UserStatus.ACTIVE.getCode()) {
    // active
}
```

或：
```java
if (userStatus == UserStatus.ACTIVE) {
    // active
}
```

---

## A-11 `long` / `Long` 字面值一律使用大寫 `L`

**規則**
- 所有 `long` 或 `Long` 常值尾碼都使用大寫 `L`。
- 不要使用小寫 `l`。

**原因**
- 小寫 `l` 容易被誤看成數字 `1`。

**反例**
```java
long orderId = 12345678901l;
Long timeout = 1l;
```

**正例**
```java
long orderId = 12345678901L;
Long timeout = 1L;
```

---

## A-12 若值域固定且需要附帶屬性，優先使用 enum

**規則**
- 若某個概念具有固定值域，且每個值還帶有 code、desc、label、priority 等屬性，優先使用 enum 封裝。

**原因**
- 可把狀態與其屬性集中管理，減少散落常數與重複判斷。

**反例**
```java
public static final int STATUS_ACTIVE = 1;
public static final int STATUS_DISABLED = 2;
```

**正例**
```java
public enum UserStatus {
    ACTIVE(1, "active"),
    DISABLED(2, "disabled");

    private final int code;
    private final String description;

    UserStatus(int code, String description) {
        this.code = code;
        this.description = description;
    }

    public int getCode() {
        return code;
    }

    public String getDescription() {
        return description;
    }
}
```

---

# B 區：OOP & 基礎語言使用

## B-1 `equals` 比較應由常量或保證非 null 的對象發起

**規則**
- 做內容比較時，優先由常量或保證非 null 的對象呼叫 `equals()`。
- 不要讓可能為 `null` 的變數主動呼叫 `equals()`。

**原因**
- 可直接降低 `NullPointerException` 風險。

**反例**
```java
if (user.getStatus().equals("ACTIVE")) {
    ...
}
```

**正例**
```java
if ("ACTIVE".equals(user.getStatus())) {
    ...
}
```

---

## B-2 包裝型別比較內容不可用 `==`

**規則**
- `Integer`、`Long`、`Boolean` 等包裝型別比較內容時，一律使用 `equals()` 或 `Objects.equals()`。
- 不要用 `==` 比較包裝型別的值。
- 若兩側任一方可能為 `null`，應使用 `Objects.equals(a, b)`。

**原因**
- `==` 比較的是參考，容易得到不穩定或錯誤的判斷結果。

**反例**
```java
Integer a = 128;
Integer b = 128;
if (a == b) {
    System.out.println("equal");
}
```

**正例**
```java
Integer a = 128;
Integer b = 128;
if (Objects.equals(a, b)) {
    System.out.println("equal");
}
```

---

## B-3 覆寫 `equals()` 時必須同步覆寫 `hashCode()`

**規則**
- 只要覆寫 `equals()`，就必須同步覆寫 `hashCode()`。
- 若類型會作為 `Map` key、`Set` 元素、去重依據或快取 key，更要確保兩者依據相同欄位。
- 若使用 Lombok `@EqualsAndHashCode`，必須確認包含欄位符合業務語意，避免把 mutable field、敏感欄位或不穩定欄位納入 equals / hashCode。

**原因**
- 否則 `HashMap`、`HashSet` 等集合的查找、去重與取值行為可能出錯。

**反例**
```java
class User {
    private Long id;

    @Override
    public boolean equals(Object obj) {
        ...
    }
}
```

**正例**
```java
class User {
    private Long id;

    @Override
    public boolean equals(Object obj) {
        ...
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}
```

---

## B-4 相同商業意義的方法命名應一致

**規則**
- 對相同商業意義的方法，應使用一致的動詞前綴。
- 例如單筆查詢用 `get`，多筆查詢用 `list`，統計用 `count`，更新用 `update`。

**原因**
- 可降低語意漂移，提升可讀性、可搜尋性與後續維護穩定性。

**反例**
```java
User getUserById(Long id);
Order findOrderById(Long id);
Product queryProductById(Long id);
```

**正例**
```java
User getUserById(Long id);
Order getOrderById(Long id);
Product getProductById(Long id);
```

---

## B-5 方法應盡量只處理一件事，並保持低耦合

**規則**
- 一個方法應盡量只處理一件事，避免同時承擔多種責任。
- 若一個方法同時處理驗證、查詢、轉換、持久化、通知、回應組裝等多種責任，應拆分成語意清楚的方法。
- 方法是否需要拆分，不應只以行數判斷；但若一個方法超過約 30～50 行，或同時包含 3 種以上不同類型的行為（例如驗證 / IO / 狀態改變 / 通知），應主動檢查是否違反單一職責。
- 拆分後的方法應以清楚邊界互相協作，避免高耦合與隱性副作用。


**原因**
- 可降低耦合，提升可讀性、可測試性與可維護性。

**反例**
```java
public OrderResult createOrder(CreateOrderRequest request) {
    // validation
    // query user
    // build order
    // insert order
    // log
    // notify
    // build response
}
```

**正例**
```java
public OrderResult createOrder(CreateOrderRequest request) {
    validateCreateOrderRequest(request);
    User user = getRequiredUser(request.getUserId());
    Order order = buildOrder(request, user);
    orderDao.insert(order);
    logOrderCreated(user, order);
    notifyOrderCreated(user, order);
    return buildOrderResult(order);
}
```

---

# C 區：Collections & Generics

## C-1 不要在 `foreach` 中直接增刪集合元素

**規則**
- 不要在 `foreach` 迴圈中直接對同一個集合做 `add()` 或 `remove()`。
- 若需要刪除元素，使用 `Iterator.remove()`。

**原因**
- 可能導致 `ConcurrentModificationException` 或 unexpected result。

**反例**
```java
for (String item : list) {
    if ("1".equals(item)) {
        list.remove(item);
    }
}
```

**正例**
```java
Iterator<String> it = list.iterator();
while (it.hasNext()) {
    String item = it.next();
    if ("1".equals(item)) {
        it.remove();
    }
}
```

---

## C-2 `Arrays.asList()` 的結果不可做 `add/remove/clear`

**規則**
- 不要把 `Arrays.asList()` 回傳的結果當成可自由增刪的 `List`。
- 若後續需要修改大小，先包成 `new ArrayList<>(...)`。

**原因**
- `Arrays.asList()` 回傳的是固定大小的 List，對其做 `add/remove/clear` 會丟出 `UnsupportedOperationException`。

**反例**
```java
List<String> list = Arrays.asList("a", "b", "c");
list.add("d");
```

**正例**
```java
List<String> list = new ArrayList<>(Arrays.asList("a", "b", "c"));
list.add("d");
```

---

## C-3 集合轉陣列時使用 `toArray(T[] array)` 的安全寫法

**規則**
- 集合轉陣列時，使用 `toArray(new T[0])` 或等價的帶型別寫法。
- 不要使用無參數 `toArray()` 再自行強制轉型。

**原因**
- 無參數 `toArray()` 回傳的是 `Object[]`，強轉成具體型別陣列可能導致 `ClassCastException`。

**反例**
```java
String[] array = (String[]) list.toArray();
```

**正例**
```java
String[] array = list.toArray(new String[0]);
```

---

## C-4 泛型不要省略型別資訊

**規則**
- 使用集合時不要使用 raw type。
- `List`、`Set`、`Map` 等都應明確標示泛型型別。

**原因**
- 可提升型別安全，把錯誤盡量提前到編譯期，而不是執行期才出現 `ClassCastException`。

**反例**
```java
List list = new ArrayList();
list.add("hello");
list.add(123);
```

**正例**
```java
List<String> list = new ArrayList<>();
list.add("hello");
```

---

# D 區：Concurrency

## D-1 建立執行緒池不要用 `Executors`，改用 `ThreadPoolExecutor`

**規則**
- 禁止使用 `Executors.newFixedThreadPool()`、`newCachedThreadPool()`、`newSingleThreadExecutor()`、`newScheduledThreadPool()` 直接建立執行緒池。
- 必須使用 `ThreadPoolExecutor` 顯式設定執行緒數、佇列容量與拒絕策略。
- 若使用 Java virtual thread 或框架管理的 executor，必須確認生命週期、併發邊界、監控與關閉流程，不得未評估就套用本規則的傳統 thread pool 範例。
- 本規則主要適用於長期運行的業務程式；單元測試、POC / Demo、JVM 生命週期極短的工具程式可例外，但需有明確理由。

**原因**
- 某些 `Executors` 預設配置可能導致 queue 過大或執行緒數過大，最後造成 OOM。

**反例**
```java
ExecutorService executor = Executors.newFixedThreadPool(10);
```

**正例**
```java
ExecutorService executor = new ThreadPoolExecutor(
    10,
    20,
    60L,
    TimeUnit.SECONDS,
    new ArrayBlockingQueue<>(100),
    new ThreadPoolExecutor.CallerRunsPolicy()
);
```

---

## D-2 `ThreadLocal` 使用完必須 `remove()`

**規則**
- 使用 `ThreadLocal` 時，`set()` 後必須搭配 `try/finally`，並在 `finally` 裡呼叫 `remove()`。
- 在執行緒池任務中特別要遵守。

**原因**
- 避免資料殘留、跨請求污染，並降低記憶體洩漏風險。

**反例**
```java
private static final ThreadLocal<String> CURRENT_USER = new ThreadLocal<>();

public void handleRequest(String userId) {
    CURRENT_USER.set(userId);
    doBusiness();
}
```

**正例**
```java
private static final ThreadLocal<String> CURRENT_USER = new ThreadLocal<>();

public void handleRequest(String userId) {
    try {
        CURRENT_USER.set(userId);
        doBusiness();
    } finally {
        CURRENT_USER.remove();
    }
}
```

---

## D-3 共用可變狀態要避免競態，必要時選對同步或並發容器

**規則**
- 若多個執行緒會同時讀寫同一份可變資料，必須明確採用同步機制、原子類型、並發容器，或改寫為不共享可變狀態。
- 不得假設一般欄位遞增、`HashMap` 寫入、狀態更新在多執行緒下天然安全。
- 若類別為 singleton（例如常見的 Spring singleton bean），或可能被多執行緒同時呼叫，應視為本規則適用範圍。

**原因**
- 多執行緒下的讀改寫可能互相覆蓋，導致資料不一致、計數錯誤、狀態錯亂等問題。

**反例**
```java
public class CounterService {
    private int count = 0;

    public void increment() {
        count++;
    }
}
```

**正例**
```java
public class CounterService {
    private final AtomicInteger count = new AtomicInteger(0);

    public void increment() {
        count.incrementAndGet();
    }
}
```

---

## D-4 不要在沒有邊界與監控下隨意建立執行緒

**規則**
- 除非有明確理由，禁止在業務程式中直接 `new Thread()`。
- 背景任務應透過受控的執行緒池執行，並明確設定併發上限、佇列上限、拒絕策略與關閉流程。
- 若涉及長期運行工作，應提供可識別的 thread naming 與基本監控資訊。

**原因**
- 執行緒不是免費資源。若沒有邊界與管理，可能造成執行緒數暴增、任務堆積、難以監控與排查問題。

**反例**
```java
public void handleTask(Task task) {
    new Thread(() -> doWork(task)).start();
}
```

**正例**
```java
private final ExecutorService executor = new ThreadPoolExecutor(
    4,
    8,
    60L,
    TimeUnit.SECONDS,
    new ArrayBlockingQueue<>(200),
    new ThreadPoolExecutor.CallerRunsPolicy()
);

public void sendEmails(List<EmailTask> tasks) {
    for (EmailTask task : tasks) {
        executor.execute(() -> emailService.send(task));
    }
}
```

---

# E 區：Exceptions & Resource Management

## E-1 例外不可吞掉；不處理就往上拋

**規則**
- 禁止空的 `catch` 區塊。
- 捕獲例外後，必須明確處理、保留足夠上下文並重新拋出，或在邊界層轉換成可理解的業務結果。
- 不得無聲忽略例外。
- 僅允許在已轉換為明確業務結果，或已記錄錯誤並明確決定忽略（且有註解說明原因）的情況下不往外拋。

**原因**
- 避免錯誤被隱藏、狀態不一致、排查困難。

**反例**
```java
try {
    doSomething();
} catch (Exception e) {
}
```

**正例**
```java
try {
    userDao.insert(user);
} catch (Exception e) {
    throw new RuntimeException("Failed to save user", e);
}
```

---

## E-2 最上層例外處理要轉成可理解、可追蹤的結果

**規則**
- 在 controller、API、job、consumer 等邊界層，例外應轉換成穩定且可理解的錯誤結果。
- 不得直接向外暴露底層技術例外細節。
- 同時必須保留足夠的內部日誌上下文與原始例外鏈。

**原因**
- 避免對外暴露技術細節，並提高錯誤回應的可理解性與內部可追蹤性。

**反例**
```java
@PostMapping("/orders")
public String createOrder(@RequestBody CreateOrderRequest request) {
    try {
        orderService.createOrder(request);
        return "ok";
    } catch (Exception e) {
        return e.getMessage();
    }
}
```

**正例**
```java
@PostMapping("/orders")
public ApiResponse<Void> createOrder(@RequestBody CreateOrderRequest request) {
    try {
        orderService.createOrder(request);
        return ApiResponse.success();
    } catch (InvalidOrderException e) {
        return ApiResponse.fail("INVALID_ORDER", "Order data is invalid");
    } catch (Exception e) {
        log.error("Failed to create order, request={}", request, e);
        return ApiResponse.fail("INTERNAL_ERROR", "System is busy, please try again later");
    }
}
```

---

## E-3 優先使用 try-with-resources 管理可關閉資源

**規則**
- 任何實作 `AutoCloseable` 的資源，預設使用 try-with-resources 管理。
- 不得只在正常路徑手動 `close()`。

**原因**
- 可確保不論正常或異常流程都能正確釋放資源，降低資源洩漏風險。

**反例**
```java
public String readFile(String path) throws IOException {
    BufferedReader reader = new BufferedReader(new FileReader(path));
    String line = reader.readLine();
    reader.close();
    return line;
}
```

**正例**
```java
public String readFile(String path) throws IOException {
    try (BufferedReader reader = new BufferedReader(new FileReader(path))) {
        return reader.readLine();
    }
}
```

---

## E-4 `finally` 區塊中禁止 `return`

**規則**
- `finally` 區塊中不得出現 `return`。
- `finally` 只能做清理、釋放與收尾，不得改變方法原本的回傳或例外傳遞行為。

**原因**
- 避免吞掉原始例外或覆蓋原本的回傳值。

**反例**
```java
public int test() {
    try {
        return 1;
    } finally {
        return 2;
    }
}
```

**正例**
```java
public int test() {
    try {
        return 1;
    } finally {
        cleanUp();
    }
}
```

---

## E-5 `finally` 中不要再丟新例外或覆蓋原錯誤

**規則**
- `finally` 區塊只允許做清理與收尾。
- 不得在 `finally` 中丟出新的例外來覆蓋 `try/catch` 中原本的原始錯誤。

**原因**
- 避免真正的 root cause 被遮蔽，造成排查方向偏移。

**反例**
```java
public void test() {
    try {
        throw new RuntimeException("original error");
    } finally {
        throw new RuntimeException("cleanup error");
    }
}
```

**正例**
```java
public void doWork() {
    try {
        runBusiness();
    } finally {
        cleanUpQuietly();
    }
}
```

---

## E-6 主動防範 NPE，特別注意高風險缺值來源

**規則**
- 對可能缺值的資料來源（DB 查詢、RPC 回傳、Session、集合元素、鏈式呼叫、自動拆箱）不得直接假設非 null。
- 必須在邊界處做明確判空、轉換預設值，或轉為可理解的錯誤。

**原因**
- 可降低執行時 `NullPointerException`，特別是在異常資料或邊界條件下。

**反例**
```java
User user = userDao.findById(id);
return user.getName();
```

**正例**
```java
User user = userDao.findById(id);
if (user == null) {
    throw new UserNotFoundException("User not found");
}
return user.getName();
```

---

## E-7 `Optional` 可用於表達可能缺值的回傳，但不要濫用

**規則**
- 對「可能沒有結果」的方法回傳，可使用 `Optional` 明確表達缺值語意。
- 不得把 `Optional` 當成萬用包裝物到處套用。
- 特別避免作為 DTO/entity 欄位或一般方法參數，除非有明確設計理由。
- `Optional` 適合用於方法回傳；不建議在 Controller、DTO、Entity 之間跨層層層傳遞。
- 不得把 `Optional` 當成 null 的機械替代品。

**原因**
- 可讓呼叫端明確知道此處可能沒值，但避免把模型與方法簽名變得彆扭或過度複雜。

**反例**
```java
public class UserDTO {
    private Optional<String> name;
}
```

**正例**
```java
public Optional<User> findUserById(Long id) {
    User user = userDao.findById(id);
    return Optional.ofNullable(user);
}
```

---

# F 區：Logs

## F-1 日誌統一透過 SLF4J

**規則**
- Java 專案中的業務與應用程式碼，預設統一使用 SLF4J 作為日誌 API。
- 不得在一般業務程式中直接綁定特定 logging implementation API，除非有明確框架整合需求。

**原因**
- 可保持日誌呼叫方式一致、降低耦合，並提升專案整體可維護性。

**反例**
```java
import org.apache.log4j.Logger;

public class UserService {
    private static final Logger logger = Logger.getLogger(UserService.class);
}
```

**正例**
```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class UserService {
    private static final Logger log = LoggerFactory.getLogger(UserService.class);
}
```

---

## F-2 記錄例外時，要同時留下原始例外物件與足夠業務上下文

**規則**
- 捕獲例外並記錄日誌時，必須同時記錄必要上下文與原始例外物件。
- 不得只記固定字串。
- 不得只記 `e.getMessage()` 而遺失 stack trace。
- 日誌中應包含足以定位問題的關鍵業務上下文，例如 `requestId`、`userId`、`orderId`、`jobId`、`tenantId` 或關鍵參數。
- 上下文應精簡且有辨識價值，避免無差別傾倒整個物件。

**原因**
- 同時保留 stack trace 與業務上下文，才能讓錯誤既能看見技術呼叫鏈，也能快速定位到具體業務場景。

**反例**
```java
catch (Exception e) {
    log.error("create order failed");
}
```

```java
catch (Exception e) {
    log.error("create order failed: {}", e.getMessage());
}
```

**正例**
```java
catch (Exception e) {
    log.error("create order failed, orderId={}, userId={}, requestId={}", orderId, userId, requestId, e);
}
```

---

## F-3 避免在高頻路徑做大量無條件字串拼接日誌

**規則**
- 日誌輸出預設使用參數化寫法，不得使用無條件字串拼接。
- 若日誌參數需要昂貴計算、序列化或大型物件展開，必須先用對應 log level 判斷再執行。

**原因**
- 避免在高頻路徑中，即使 log level 沒開，仍然先付出字串拼接、序列化或重計算成本。

**反例**
```java
log.debug("user info: " + user);
log.debug("response={}", objectMapper.writeValueAsString(response));
```

**正例**
```java
log.debug("user info: {}", user);

if (log.isDebugEnabled()) {
    log.debug("response={}", objectMapper.writeValueAsString(response));
}
```

---

# G 區：SQL / ORM / Database

## G-1 有唯一性要求的資料，資料庫層必須建立唯一索引

**規則**
- 任何具有業務唯一性要求的欄位或欄位組合，必須在資料庫層建立唯一索引或唯一約束。
- 不得僅依賴應用層查重邏輯保證唯一性。
- 應用層查重只能作為友善提示，不可取代資料庫約束。

**原因**
- 可避免併發下查重失效，防止資料重複、資料髒掉與後續業務規則被破壞。

**反例**
```java
User existing = userDao.findByEmail(email);
if (existing == null) {
    userDao.insert(newUser);
}
```

**正例**
```sql
CREATE UNIQUE INDEX uk_user_email ON user(email);
```

```java
try {
    userDao.insert(new User(email));
} catch (DuplicateKeyException e) {
    throw new BusinessException("Email already exists", e);
}
```

---

## G-2 JOIN 欄位型別必須一致，且要有索引

**規則**
- 設計或使用 JOIN 時，兩側關聯欄位必須採用相同資料型別。
- 關聯欄位必須存在適當索引。
- 不得依賴隱性型別轉換進行 JOIN。

**原因**
- 可降低 JOIN 效能風險，避免因型別不一致造成索引利用變差或查詢行為異常。

**反例**
```sql
-- users.id 是 bigint
-- orders.user_id 是 varchar
select *
from orders o
join users u on o.user_id = u.id;
```

**正例**
```sql
-- users.id 與 orders.user_id 都是 bigint
select *
from orders o
join users u on o.user_id = u.id;
```

```sql
create index idx_orders_user_id on orders(user_id);
```

---

## G-3 核心交易與高頻 OLTP 查詢應避免過多 JOIN

**規則**
- 核心交易與高頻 OLTP 查詢，單條 SQL 原則上不得超過三表 JOIN。
- 若業務需求需要跨更多資料實體，應優先考慮拆查詢、調整資料模型、增加冗餘欄位、快取、read model、view、預聚合表或其他更可維護的方案。
- 若超過三表 JOIN，必須確認查詢目的、索引、資料量、執行計畫與維護性，不得只因一次查完較方便就放大 SQL 複雜度。
- 三表指的是實際 JOIN 的資料表數量；若因 legacy schema 無法避免，應優先考慮 view、預聚合表或其他可控方案。

**原因**
- 可避免查詢複雜度、效能風險與維護難度快速失控。

**反例**
```sql
select o.id, u.name, m.name, c.code, r.region_name
from orders o
join users u on o.user_id = u.id
join merchants m on o.merchant_id = m.id
join coupons c on o.coupon_id = c.id
join regions r on u.region_id = r.id
where o.id = ?
```

**正例**
```sql
select o.id, o.user_id, o.merchant_id, o.coupon_id
from orders o
where o.id = ?
```

---

## G-4 分頁查詢中禁止使用前置萬用字元 `LIKE`

**規則**
- 分頁查詢中禁止使用前置萬用字元 `LIKE`，例如 `LIKE '%keyword'` 或 `LIKE '%keyword%'`。
- 若需要包含式模糊搜尋，應優先考慮搜尋引擎或其他更適合的檢索方案。

**原因**
- 前置 `%` 通常難以有效利用索引，資料量一大時容易導致分頁查詢變慢。

**反例**
```sql
select id, name
from product
where name like '%phone%'
order by id desc
limit 20 offset 0
```

**正例**
```sql
select id, name
from product
where name like 'phone%'
order by id desc
limit 20 offset 0
```

---

## G-5 ORM / SQL 參數綁定不可用 `${}` 取代 `#{}`

**規則**
- 在 MyBatis / ORM SQL 中，凡是來自外部輸入的條件值，一律使用 `#{}` 參數綁定。
- 禁止使用 `${}` 直接拼接使用者輸入。
- 若少數場景必須用 `${}`，必須限定為受控白名單內容，例如經嚴格枚舉校驗的欄位名或排序方向。

**原因**
- `${}` 直接拼接字串會引入 SQL injection 風險，`#{}` 才是安全的參數綁定方式。

**反例**
```xml
<select id="findUser">
  select * from user where name = '${name}'
</select>
```

**正例**
```xml
<select id="findUser">
  select * from user where name = #{name}
</select>
```

---

## G-6 不要把查詢結果直接映成 `HashMap/HashTable`

**規則**
- ORM / DAO 查詢結果不得默認使用 `HashMap` / `Hashtable` 等鬆散結構承載。
- 必須使用明確的 DO / Entity / DTO 類型與對應 mapping。
- 只有在動態欄位、報表聚合或明確無固定結構的少數場景下，才可受控地使用 Map。

**原因**
- 可提升型別安全、結構語意與後續維護性，避免 magic string 與執行期 cast 風險。

**反例**
```java
Map<String, Object> userMap = userDao.queryUser(id);
String name = (String) userMap.get("name");
```

**正例**
```java
UserDO user = userDao.queryUser(id);
String name = user.getName();
```

---

## G-7 禁止設計通用全欄位更新

**規則**
- 禁止設計默認全欄位更新的 DAO / mapper。
- 更新語句必須只包含本次業務明確需要變更的欄位。
- 不得因物件帶入空值、預設值或舊值而覆蓋其他未打算修改的資料。

**原因**
- 可避免資料誤覆蓋、降低不必要的寫入成本，並減少 binlog / 資料庫負擔。

**反例**
```sql
update user
set name = ?,
    age = ?,
    phone = ?,
    email = ?,
    address = ?,
    status = ?
where id = ?
```

**正例**
```sql
update user
set phone = ?
where id = ?
```

---

## G-8 SQL / ORM 設計要偏向明確欄位、明確模型、明確映射

**規則**
- 查詢不得使用 `select *`。
- 查詢結果不得依賴鬆散結構或直接 `resultClass` 偷懶映射。
- 必須透過明確的 DO / Entity / DTO 與 `resultMap` / mapping 維持欄位、資料表與 Java 類之間的可維護解耦。

**原因**
- 可避免查詢拿太多不需要的欄位、減少隱式對應風險，並讓資料表欄位與 Java 模型維持清楚且可維護的映射關係。

**反例**
```xml
<select id="queryUser" resultClass="UserDO">
  select * from user where id = #{id}
</select>
```

**正例**
```xml
<resultMap id="userResultMap" type="UserDO">
    <id property="id" column="id"/>
    <result property="userName" column="user_name"/>
    <result property="phoneNo" column="phone_no"/>
    <result property="deleted" column="is_deleted"/>
</resultMap>

<select id="queryUser" resultMap="userResultMap">
    select id, user_name, phone_no, is_deleted
    from user
    where id = #{id}
</select>
```

---

# H 區：Security

## H-1 使用者自己的頁面或功能，必須做授權檢查

**規則**
- 任何存取使用者個人資料、角色限制功能、檔案、訂單、帳戶或其他受保護資源的 API，都必須在後端做授權檢查。
- 不可只依賴 URL、request parameter、前端畫面控制或傳入的 `userId` / `resourceId` 判斷權限。
- 只要資料或操作屬於特定使用者、特定角色或特定權限範圍，就必須確認目前登入者是否有權存取。
- 權限檢查應盡量收斂到共用授權元件、service 方法或明確的權限檢查流程中，避免每支 API 各自手寫且邏輯不一致。

**原因**
- 避免越權存取。
- 使用者可能竄改 URL 或 API 參數，例如改 `userId`、`orderId`、`accountId`，嘗試讀取或操作不屬於自己的資料。
- 前端隱藏按鈕或限制畫面入口不等於安全控制，真正的授權必須在後端執行。

**反例**
```java
@GetMapping("/orders/{orderId}")
public OrderDTO getOrder(@PathVariable Long orderId) {
    return orderService.getOrder(orderId);
}
```

**正例**
```java
@GetMapping("/orders/{orderId}")
public OrderDTO getOrder(
        @PathVariable Long orderId,
        @AuthenticationPrincipal LoginUser loginUser) {

    return orderService.getOrderForUser(orderId, loginUser.getUserId());
}
```

```java
public OrderDTO getOrderForUser(Long orderId, Long userId) {
    Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new NotFoundException("Order not found"));

    if (!order.getUserId().equals(userId)) {
        throw new AccessDeniedException("No permission to access this order");
    }

    return OrderDTO.from(order);
}
```

---

## H-2 敏感資料不可直接展示，必須最小化與脫敏

**規則**
- 不得直接回傳或展示完整敏感資料。
- 產生 API response、頁面資料、log、錯誤訊息、匯出檔或通知內容時，必須先判斷欄位是否真的必要。
- 不必要的敏感欄位不得輸出。
- 必要輸出的敏感欄位，必須使用遮罩、截斷、部分顯示或其他脫敏方式。
- 不得直接回傳 Entity 作為 API response。
- 不得無差別記錄完整 request、response、entity 或 user object。
- 常見敏感資料包含：身分證字號、手機、Email、地址、卡號、帳號、Token、密碼、憑證、金鑰、個資、交易相關資料。

**原因**
- 避免個資、帳號、憑證與交易資料外洩。
- 降低 log、API、報表、通知外流時的安全與合規風險。
- 脫敏不是保證完全沒有資訊揭露，而是降低完整敏感資料被取得的風險。
- 最安全的資料處理方式是不要輸出；其次才是遮罩後輸出。

**反例**
```java
public UserProfileDTO getProfile(Long userId) {
    User user = userRepository.findById(userId)
            .orElseThrow(() -> new UserNotFoundException("User not found"));

    return new UserProfileDTO(
            user.getName(),
            user.getMobile(),
            user.getEmail(),
            user.getIdNo(),
            user.getCardNo()
    );
}
```

```java
log.info("create user success, user={}", user);
```

**正例**
```java
public UserProfileDTO getProfile(Long userId) {
    User user = userRepository.findById(userId)
            .orElseThrow(() -> new UserNotFoundException("User not found"));

    return new UserProfileDTO(
            maskName(user.getName()),
            maskMobile(user.getMobile()),
            maskEmail(user.getEmail())
    );
}
```

```java
private String maskMobile(String mobile) {
    if (mobile == null || mobile.length() < 7) {
        return "****";
    }
    return mobile.substring(0, 3)
            + "****"
            + mobile.substring(mobile.length() - 3);
}
```

```java
private String maskCardNo(String cardNo) {
    if (cardNo == null || cardNo.length() < 4) {
        return "****";
    }
    return "**** **** **** " + cardNo.substring(cardNo.length() - 4);
}
```

```java
log.info("create user success, userId={}, mobile={}",
        user.getId(),
        maskMobile(user.getMobile()));
```

**補充說明**
- 遮罩後的資料仍然是資訊揭露，只是沒有揭露完整敏感資料。
- 若前端不需要某個敏感欄位，應完全不回傳，而不是只做遮罩。
- 脫敏方法不會改變資料庫中的原始資料，只會改變本次輸出的字串。

---

## H-3 使用者資料輸出到 HTML 前必須 escaping 或安全過濾

**規則**
- 使用者資料可以接收與使用，但不得未經處理就輸出到 HTML。
- 若資料只是作為文字顯示，必須做 HTML escaping。
- 若業務允許輸入部分 HTML，必須經過白名單式 security filtering / sanitizer。
- 禁止把使用者輸入直接拼接進 HTML、JavaScript、CSS、URL 或 HTML attribute。
- 不要使用會輸出 raw HTML 的模板語法，除非該內容已經過可信任的 sanitizer 處理。

**原因**
- 避免 XSS 攻擊。
- 若使用者輸入被瀏覽器當成 HTML 或 JavaScript 執行，可能造成 Cookie、Token、個資外洩，或讓攻擊者冒用使用者操作頁面。
- Validation 與 escaping 不同：validation 是檢查輸入格式、長度、範圍；escaping 是避免輸出到 HTML 時被瀏覽器當成程式碼執行。

**反例**
```java
@GetMapping("/hello")
@ResponseBody
public String hello(@RequestParam String name) {
    return "<h1>Hello, " + name + "</h1>";
}
```

若 `name` 是：

```html
<script>alert('xss')</script>
```

輸出會變成：

```html
<h1>Hello, <script>alert('xss')</script></h1>
```

**正例**
```java
@GetMapping("/hello")
@ResponseBody
public String hello(@RequestParam String name) {
    String safeName = HtmlUtils.htmlEscape(name);
    return "<h1>Hello, " + safeName + "</h1>";
}
```

輸出會變成類似：

```html
<h1>Hello, &lt;script&gt;alert('xss')&lt;/script&gt;</h1>
```

若使用模板引擎，優先使用會自動 escaping 的輸出語法：

```html
<p th:text="${name}"></p>
```

避免未經安全處理就使用 raw HTML 輸出：

```html
<p th:utext="${name}"></p>
```

---

## H-4 表單提交與 AJAX 請求必須做 CSRF 防護

**規則**
- 表單提交與 AJAX 請求必須經過 CSRF security check。
- 若 API 完全不依賴瀏覽器自動攜帶的 cookie / session，而是使用 Authorization header 等非自動附帶憑證，應依實際認證模型評估 CSRF 需求；但不得在未確認認證模型前移除 CSRF 防護。
- 對任何會新增、修改、刪除資料，或會影響帳號、權限、交易、設定的請求，不得只依賴登入狀態。
- CSRF 檢查應優先由框架、filter、interceptor 或共用安全元件統一處理，避免每支 API 手寫導致遺漏。
- 產生表單或 AJAX 範例時，必須保留 CSRF token 傳遞與後端驗證流程。

**原因**
- 避免攻擊者誘導已登入使用者，在不知情的情況下發出偽造請求，造成資料、設定、權限或交易被修改。
- CSRF 的風險在於：攻擊者不一定需要知道使用者密碼，只要使用者瀏覽器仍帶有登入 cookie，就可能被利用。

**反例**
```java
@PostMapping("/profile/mobile")
public ApiResponse<Void> updateMobile(@RequestParam String mobile,
                                      @AuthenticationPrincipal LoginUser loginUser) {
    userService.updateMobile(loginUser.getUserId(), mobile);
    return ApiResponse.success();
}
```

攻擊者可能在第三方頁面中誘導瀏覽器送出請求：

```html
<form action="https://example.com/profile/mobile" method="post">
    <input type="hidden" name="mobile" value="0911111111">
</form>
<script>
    document.forms[0].submit();
</script>
```

**正例**
```java
@PostMapping("/profile/mobile")
public ApiResponse<Void> updateMobile(@RequestBody UpdateMobileRequest request,
                                      @AuthenticationPrincipal LoginUser loginUser) {
    // CSRF check is enforced by security filter/interceptor before entering this method.
    userService.updateMobile(loginUser.getUserId(), request.getMobile());
    return ApiResponse.success();
}
```

表單提交時攜帶 CSRF token：

```html
<form action="/profile/mobile" method="post">
    <input type="hidden" name="csrfToken" value="${csrfToken}">
    <input type="text" name="mobile">
    <button type="submit">Save</button>
</form>
```

AJAX 請求時攜帶 CSRF token：

```javascript
fetch("/profile/mobile", {
    method: "POST",
    headers: {
        "Content-Type": "application/json",
        "X-CSRF-TOKEN": csrfToken
    },
    body: JSON.stringify({
        mobile: "0912345678"
    })
});
```

---

## H-5 影響資料或權限的 API 不可只依賴前端限制

**規則**
- 任何會新增、修改、刪除資料，或影響帳號、權限、交易、設定、狀態的 API，都必須在後端再次驗證。
- 不得只依賴前端按鈕是否顯示、欄位是否 disabled、頁面是否隱藏或下拉選單是否限制。
- 後端不得直接相信 request 中的 `role`、`permission`、`status`、`amount`、`ownerId`、`userId`、`accountId`、`tenantId`、`isAdmin` 等敏感欄位。
- 一般使用者 API 與管理員 API 應明確分離。
- 後端必須重新檢查目前登入者權限、request 參數合法性、操作目標是否可修改、狀態流轉是否合法。

**原因**
- 前端限制只是使用者體驗，不是安全邊界。
- 使用者可以透過 DevTools、Postman、curl 或代理工具修改 request 並直接呼叫 API。
- 後端驗證才能真正防止越權、資料竄改與非法狀態變更。

**反例**
```java
public class UpdateUserRequest {
    private String name;
    private String mobile;
    private String role;
    private String status;
}
```

```java
public void updateUser(Long userId, UpdateUserRequest request) {
    User user = userRepository.findById(userId)
            .orElseThrow(() -> new UserNotFoundException("User not found"));

    user.setName(request.getName());
    user.setMobile(request.getMobile());
    user.setRole(request.getRole());
    user.setStatus(request.getStatus());

    userRepository.save(user);
}
```

**正例**
```java
public class UpdateUserProfileRequest {
    private String name;
    private String mobile;
}
```

```java
@PostMapping("/users/{userId}/profile")
public ApiResponse<Void> updateProfile(@PathVariable Long userId,
                                       @RequestBody UpdateUserProfileRequest request,
                                       @AuthenticationPrincipal LoginUser loginUser) {
    if (!loginUser.getUserId().equals(userId)) {
        throw new AccessDeniedException("No permission to update this profile");
    }

    userService.updateProfile(userId, request);
    return ApiResponse.success();
}
```

```java
public void updateProfile(Long userId, UpdateUserProfileRequest request) {
    User user = userRepository.findById(userId)
            .orElseThrow(() -> new UserNotFoundException("User not found"));

    user.setName(request.getName());
    user.setMobile(request.getMobile());

    userRepository.save(user);
}
```

---

# I 區：Other Basic Rules

## I-1 正則表達式應預編譯，不要在熱路徑反覆 `Pattern.compile()`

**規則**
- 同一個正則表達式如果會被重複使用，必須預先編譯成可重用的 `Pattern`。
- 不要在迴圈、批次處理、大量請求、熱路徑中反覆呼叫 `Pattern.compile()`。
- 預編譯的 `Pattern` 優先宣告為 `private static final` 常數。
- 若正則只使用一次，或明確是低頻臨時邏輯，可視情境放寬。

**原因**
- `Pattern.compile()` 會把正則字串編譯成可執行的匹配結構。
- 如果每次請求或每筆資料都重新 compile，會造成不必要的 CPU、物件建立與 GC 成本。
- 將正則集中為常數，也能提升可讀性與維護性。

**反例**
```java
public boolean isValidMobile(String mobile) {
    if (mobile == null) {
        return false;
    }

    return Pattern.compile("^09\\d{8}$")
            .matcher(mobile)
            .matches();
}
```

**正例**
```java
private static final Pattern MOBILE_PATTERN = Pattern.compile("^09\\d{8}$");

public boolean isValidMobile(String mobile) {
    if (mobile == null) {
        return false;
    }

    return MOBILE_PATTERN.matcher(mobile).matches();
}
```

**批次處理反例**
```java
public List<String> filterValidMobiles(List<String> mobiles) {
    List<String> result = new ArrayList<>();

    for (String mobile : mobiles) {
        if (Pattern.compile("^09\\d{8}$").matcher(mobile).matches()) {
            result.add(mobile);
        }
    }

    return result;
}
```

**批次處理正例**
```java
private static final Pattern MOBILE_PATTERN = Pattern.compile("^09\\d{8}$");

public List<String> filterValidMobiles(List<String> mobiles) {
    List<String> result = new ArrayList<>();

    for (String mobile : mobiles) {
        if (mobile != null && MOBILE_PATTERN.matcher(mobile).matches()) {
            result.add(mobile);
        }
    }

    return result;
}
```

---

## I-2 產生隨機整數時使用 Random API，不要用 `Math.random()` 乘完再 round

**規則**
- 要產生隨機整數時，不得使用 `Math.random() * n` 再搭配 `Math.round()`。
- 應使用 `Random.nextInt(bound)`、`Random.nextLong()`，或在多執行緒場景使用 `ThreadLocalRandom.current().nextInt(...)`。
- 產生範圍時必須明確寫出上下界語意，例如 `nextInt(10)` 表示 `0 <= value < 10`。
- 若用途涉及安全性，例如驗證碼、Token、密碼重設碼、交易 nonce，應使用 `SecureRandom`，不得使用一般 `Random` 或 `Math.random()`。

**原因**
- 避免隨機整數範圍錯誤、邊界分布不直覺與 off-by-one error。
- 專用 API 語意更清楚，也更容易維護。
- 多執行緒場景使用 `ThreadLocalRandom` 可避免共用 `Random` 的競爭問題。
- 安全敏感用途需要安全隨機來源。

**反例**
```java
public int randomDigit() {
    return (int) Math.round(Math.random() * 10);
}
```

**問題說明**
- 這段會產生 `0` 到 `10`，不一定是開發者原本以為的 `0` 到 `9`。
- 使用 `round` 時，邊界值的分布不如 `nextInt(bound)` 直覺。

**正例**
```java
private final Random random = new Random();

public int randomDigit() {
    return random.nextInt(10);
}
```

這表示：

```text
0 <= value < 10
```

如果要產生 `1` 到 `10`：

```java
private final Random random = new Random();

public int randomOneToTen() {
    return random.nextInt(10) + 1;
}
```

**多執行緒正例**
```java
public int generateSixDigitCode() {
    return ThreadLocalRandom.current().nextInt(100_000, 1_000_000);
}
```

這表示：

```text
100000 <= value < 1000000
```

也就是一定是 6 位數。

**安全用途反例**
```java
public String generateResetToken() {
    return String.valueOf(ThreadLocalRandom.current().nextLong());
}
```

**安全用途正例**
```java
private static final SecureRandom SECURE_RANDOM = new SecureRandom();

public String generateResetToken() {
    byte[] bytes = new byte[32];
    SECURE_RANDOM.nextBytes(bytes);
    return Base64.getUrlEncoder()
            .withoutPadding()
            .encodeToString(bytes);
}
```

---

## I-3 程式碼風格應維持機械一致

**規則**
- Java 程式碼必須維持一致的括號、空白、縮排、換行與行寬風格。
- 縮排使用 4 個 spaces，不使用 tab。
- 單行長度不要超過 120 個字元。
- `if`、`for`、`while`、`switch` 等控制語句，即使只有一行，也必須使用大括號。
- 運算子前後、逗號後面、關鍵字與括號之間，必須保留一致空白。
- 不要把多個語句壓在同一行。
- 格式規則應盡量交由 formatter、Checkstyle、IDE code style 或 CI 自動檢查。

**原因**
- 保持 codebase 風格一致，降低閱讀與 code review 成本。
- 避免格式差異造成無意義 diff。
- 避免省略大括號或縮排混亂造成維護時誤判邏輯。

**反例**
```java
public void updateUser(User user){
if(user==null){throw new IllegalArgumentException("user is null");}
if(user.isActive()) doUpdate(user);
}
```

**正例**
```java
public void updateUser(User user) {
    if (user == null) {
        throw new IllegalArgumentException("user is null");
    }

    if (user.isActive()) {
        doUpdate(user);
    }
}
```

---

## I-4 陣列型別宣告採 `String[] args`，不要 `String args[]`

**規則**
- 陣列宣告時，`[]` 必須放在型別後面。
- 使用 `String[] args`、`int[] numbers`、`UserDTO[] users`。
- 不使用 `String args[]`、`int numbers[]`、`UserDTO users[]`。
- 避免在同一行混合宣告陣列與非陣列變數。

**原因**
- 型別資訊更清楚，能明確看出變數是 array type。
- 避免 `String name, aliases[]` 這類宣告造成閱讀誤解。
- 保持 Java 陣列宣告風格一致。

**反例**
```java
public static void main(String args[]) {
    System.out.println("Hello");
}

String name, aliases[];
```

**正例**
```java
public static void main(String[] args) {
    System.out.println("Hello");
}

String name;
String[] aliases;
```

## I-5 若使用設計模式，類名可反映 pattern 角色

**規則**
- 如果類別明確扮演某個設計模式角色，類名可以反映該角色。
- 常見角色名稱包含 `Factory`、`Builder`、`Strategy`、`Adapter`、`Decorator`、`Proxy`、`Observer`、`Handler`、`Template`、`Command`。
- 類名中的 pattern 角色必須與實際責任一致。
- 不要為了看起來有架構而硬套設計模式名稱。
- 若類別只是普通業務服務、查詢、轉換或流程協調，應使用更直接的業務名稱。

**原因**
- 類名能直接表達架構角色，提升可讀性與維護性。
- 避免設計模式已存在但意圖不明。
- 同時避免 AI agent 過度設計，產生不必要的 pattern 類名。

**反例**
```java
public class UserQueryStrategy {
    public UserDTO getUserById(Long userId) {
        return userRepository.findById(userId);
    }
}
```

**正例**
```java
public class UserQueryService {
    public UserDTO getUserById(Long userId) {
        return userRepository.findById(userId);
    }
}
```

**Pattern 命名正例**
```java
public interface PaymentStrategy {
    void pay(PaymentRequest request);
}

public class CreditCardPaymentStrategy implements PaymentStrategy {
    @Override
    public void pay(PaymentRequest request) {
        // credit card payment logic
    }
}

public class PaymentStrategyFactory {
    public PaymentStrategy create(String type) {
        if ("CARD".equals(type)) {
            return new CreditCardPaymentStrategy();
        }
        throw new IllegalArgumentException("Unsupported payment type");
    }
}
```

---

## I-6 若採用 interface / implementation 分離，實作類命名應清楚一致

**規則**
- 若專案已採用 interface / implementation 分離，命名必須清楚且一致。
- Interface 名稱應表達業務能力或抽象責任，例如 `UserService`、`PaymentStrategy`。
- Implementation 名稱應清楚表達實作差異，例如 `DatabaseUserService`、`RemoteUserService`、`CachedUserService`。
- 避免使用 `Impl1`、`Impl2`、`NewImpl`、`OldImpl` 這類缺乏語意的名稱。
- 不得在沒有明確架構需求時，機械式替所有 Service / DAO 產生 interface。
- 若既有專案已有固定命名慣例，例如 `UserService` + `UserServiceImpl`，應優先遵守專案既有風格。

**原因**
- 清楚的命名能讓維護者快速辨識 interface 的抽象責任與 implementation 的實作差異。
- 避免過度抽象造成檔案數增加、跳轉成本提高與架構噪音。
- AI agent 應遵守既有專案架構，而不是自行強制導入 interface / implementation 分離。

**反例**
```java
public interface UserService {
    UserDTO getUserById(Long userId);
}

public class UserServiceImpl1 implements UserService {
    @Override
    public UserDTO getUserById(Long userId) {
        // query from database
    }
}

public class UserServiceImpl2 implements UserService {
    @Override
    public UserDTO getUserById(Long userId) {
        // query from remote API
    }
}
```

**正例**
```java
public interface UserService {
    UserDTO getUserById(Long userId);
}

public class DatabaseUserService implements UserService {
    @Override
    public UserDTO getUserById(Long userId) {
        // query from database
    }
}

public class RemoteUserService implements UserService {
    @Override
    public UserDTO getUserById(Long userId) {
        // query from remote API
    }
}
```

**不需強制拆 interface 的例子**
```java
public class OrderCreateService {
    public OrderResult createOrder(CreateOrderRequest request) {
        // create order
    }
}
```

---

# J 區：Business Logic & Domain Safety

> 目的：補強 Java 業務程式中的核心業務邏輯安全性，避免狀態錯亂、金額錯誤、重複處理、資料歸屬錯誤與交易一致性問題。
>
> 原則：業務規則必須明確、可驗證、可追蹤；不得依賴前端、request 傳入結果或隱含假設完成重要判斷。
>
> 嚴重度說明：
> - **Must**：硬性規則。違反時通常代表高風險缺陷，code review 應要求修正。
> - **Should**：強烈建議。若不採用，應有清楚的業務、架構或效能理由。

---

## J-1 業務狀態流轉必須顯式校驗

**嚴重度**：Must

**規則**
- 任何業務狀態變更前，必須檢查目前狀態是否允許執行該操作。
- 不得直接使用 request 傳入的狀態覆蓋資料庫中的狀態。
- 已終止狀態，例如 `CANCELLED`、`COMPLETED`、`FAILED`，不得再被任意改成其他狀態，除非有明確補償流程。
- 狀態流轉規則應集中在 domain method、state machine、enum 或 service 中，不要散落在多個 API 裡各自判斷。
- 狀態數量超過 3 個，或流程存在多個角色 / 多個入口時，應明確定義狀態流轉表或允許轉移集合，例如 `canCancel()`、`canPay()`、`canTransitionTo(targetStatus)`。

**Review 重點**
- 是否有直接 `setStatus(request.getStatus())` 的程式碼。
- 是否每個狀態變更都有檢查目前狀態。
- 終態是否可能被任意改回處理中或其他狀態。
- 狀態判斷是否散落在多個 controller / API 中。

**原因**
- 狀態錯亂會導致重複付款、已取消訂單被出貨、已完成流程被回滾等 production 風險。

**反例**
```java
public void updateOrderStatus(Long orderId, UpdateOrderStatusRequest request) {
    Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new OrderNotFoundException("Order not found"));

    order.setStatus(request.getStatus());
    orderRepository.save(order);
}
```

**正例**
```java
public void cancelOrder(Long orderId, Long userId) {
    Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new OrderNotFoundException("Order not found"));

    if (!order.getUserId().equals(userId)) {
        throw new AccessDeniedException("No permission to cancel this order");
    }

    if (!OrderStatus.CREATED.equals(order.getStatus())) {
        throw new BusinessException("Only created orders can be cancelled");
    }

    order.setStatus(OrderStatus.CANCELLED);
    orderRepository.save(order);
}
```

---

## J-2 金額、數量、庫存、點數等異動必須檢查邊界

**嚴重度**：Must

**規則**
- 涉及 `amount`、`balance`、`quantity`、`stock`、`points`、`quota`、`limit` 等業務數值時，必須明確檢查合法範圍。
- 常見檢查包含：不可為負、不可為零、不可超過餘額、不可超過庫存、不可超過單筆或單日限制。
- 不得只做運算後直接寫回資料庫。
- 若涉及單位或幣別，必須確認單位與幣別一致。
- `BigDecimal` 比較大小應使用 `compareTo()`，不得使用 `equals()` 判斷數值大小。
- 來自 DB、外部系統或 request 的數值欄位都應視為可能為 null 或不可信。

**Review 重點**
- 是否存在扣款、扣庫存、扣點數、扣額度後未檢查是否小於 0。
- 是否有直接使用 request 傳入數值更新餘額、庫存或點數。
- 是否混用不同單位、幣別或 scale。
- 是否用 `BigDecimal.equals()` 判斷金額大小。

**原因**
- 可避免負庫存、負餘額、超額交易、點數錯扣、幣別混算等業務資料錯誤。

**反例**
```java
public void deductBalance(Long accountId, BigDecimal amount) {
    Account account = accountRepository.findById(accountId)
            .orElseThrow(() -> new AccountNotFoundException("Account not found"));

    account.setBalance(account.getBalance().subtract(amount));
    accountRepository.save(account);
}
```

**正例**
```java
public void deductBalance(Long accountId, BigDecimal amount) {
    if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
        throw new BusinessException("Amount must be positive");
    }

    Account account = accountRepository.findById(accountId)
            .orElseThrow(() -> new AccountNotFoundException("Account not found"));

    if (account.getBalance().compareTo(amount) < 0) {
        throw new BusinessException("Insufficient balance");
    }

    account.setBalance(account.getBalance().subtract(amount));
    accountRepository.save(account);
}
```

---

## J-3 金額與精確計算必須使用 BigDecimal

**嚴重度**：Must

**規則**
- 涉及金額、利率、手續費、稅額、折扣、匯率、帳務數字等精確計算時，不得使用 `float` 或 `double`。
- 必須使用 `BigDecimal`，且以字串或整數建立精確值，不要用 `new BigDecimal(double)`。
- 除法、折扣、稅額、匯率換算等可能產生小數的計算，必須明確指定 `scale` 與 `RoundingMode`。
- 金額欄位應明確定義儲存單位與 scale，例如元 / 分、小數 2 位或 4 位。
- 不同幣別或不同精度的金額不得未經轉換直接相加、比較或儲存。
- RoundingMode 不應散落硬寫，應依業務語意集中定義。

**Review 重點**
- 是否使用 `double` / `float` 表示金額、費率或匯率。
- 是否使用 `new BigDecimal(0.1)` 之類的建構方式。
- 除法、稅額、折扣、匯率計算是否未指定 rounding。
- 是否在不同地方用不同 scale 或不同 rounding rule 計算同一種金額。

**原因**
- `float` / `double` 有二進位浮點精度問題，容易造成金額誤差；未指定 rounding 也可能導致結果不穩或直接丟出例外。

**反例**
```java
public double calculateFee(double amount) {
    return amount * 0.015;
}
```

```java
BigDecimal feeRate = new BigDecimal(0.015);
```

**正例**
```java
private static final BigDecimal FEE_RATE = new BigDecimal("0.015");
private static final int MONEY_SCALE = 2;
private static final RoundingMode MONEY_ROUNDING = RoundingMode.HALF_UP;

public BigDecimal calculateFee(BigDecimal amount) {
    if (amount == null || amount.compareTo(BigDecimal.ZERO) < 0) {
        throw new BusinessException("Amount is invalid");
    }

    return amount.multiply(FEE_RATE)
            .setScale(MONEY_SCALE, MONEY_ROUNDING);
}
```

---

## J-4 不得信任 request 傳入的業務結果欄位

**嚴重度**：Must

**規則**
- 後端必須自行計算核心業務結果，不得直接信任 request 傳入的結果型欄位。
- 常見結果型欄位包含：`totalAmount`、`finalAmount`、`discountAmount`、`fee`、`balance`、`points`、`level`、`status`、`role`、`permission`。
- request 可攜帶使用者選擇或輸入，但最終金額、折扣、狀態、權限、點數與餘額必須由後端根據可信資料計算。
- 本規則關注「結果型欄位」不可由 request 決定；權限與敏感欄位驗證另見 H-5。

**Review 重點**
- 是否把 request 的 `totalAmount`、`finalAmount`、`discountAmount` 直接寫入訂單或付款資料。
- 是否把 request 的 `role`、`status`、`balance`、`points` 作為最終結果。
- 後端是否有重新查詢商品、帳戶、優惠、費率、權限等可信資料。

**原因**
- 使用者可竄改 request。若直接相信結果欄位，可能造成少付金額、錯誤折扣、越權、錯誤狀態或帳務不一致。

**反例**
```java
public Order createOrder(CreateOrderRequest request) {
    Order order = new Order();
    order.setProductId(request.getProductId());
    order.setQuantity(request.getQuantity());
    order.setTotalAmount(request.getTotalAmount());
    order.setDiscountAmount(request.getDiscountAmount());
    order.setFinalAmount(request.getFinalAmount());
    return orderRepository.save(order);
}
```

**正例**
```java
public Order createOrder(CreateOrderRequest request) {
    Product product = productRepository.findById(request.getProductId())
            .orElseThrow(() -> new ProductNotFoundException("Product not found"));

    if (request.getQuantity() <= 0) {
        throw new BusinessException("Quantity must be positive");
    }

    BigDecimal totalAmount = product.getPrice()
            .multiply(BigDecimal.valueOf(request.getQuantity()));
    BigDecimal discountAmount = discountService.calculateDiscount(product, request.getQuantity());
    BigDecimal finalAmount = totalAmount.subtract(discountAmount)
            .setScale(2, RoundingMode.HALF_UP);

    Order order = new Order();
    order.setProductId(product.getId());
    order.setQuantity(request.getQuantity());
    order.setTotalAmount(totalAmount);
    order.setDiscountAmount(discountAmount);
    order.setFinalAmount(finalAmount);
    return orderRepository.save(order);
}
```

---

## J-5 查詢、修改、刪除前必須確認資料存在、歸屬與可操作狀態

**嚴重度**：Must

**規則**
- 對指定 id 的查詢、修改、刪除，必須先確認資料存在、歸屬正確，且目前狀態允許該操作。
- 若資料具有 `owner`、`userId`、`tenantId`、`accountId`、`branchId`、`merchantId` 等歸屬，必須確認歸屬符合目前操作上下文。
- 不得只依賴前端傳入的 id 直接執行更新或刪除。
- 若資料不存在或不屬於目前操作人，應回傳穩定且不洩漏敏感資訊的錯誤結果。

**Review 重點**
- 是否有直接 `deleteById(id)` 或 `updateById(id, request)`。
- 是否缺少 owner / userId / tenantId / branchId 驗證。
- 不存在與無權限的錯誤訊息是否洩漏敏感資訊。
- 資料目前狀態是否允許被修改或刪除。

**原因**
- 可避免錯改他人資料、越權操作、誤刪資料，以及因不存在資料造成靜默失敗。

**反例**
```java
public void deleteAddress(Long addressId) {
    addressRepository.deleteById(addressId);
}
```

**正例**
```java
public void deleteAddress(Long addressId, Long userId) {
    Address address = addressRepository.findById(addressId)
            .orElseThrow(() -> new NotFoundException("Address not found"));

    if (!address.getUserId().equals(userId)) {
        throw new AccessDeniedException("No permission to delete this address");
    }

    addressRepository.delete(address);
}
```

---

## J-6 不可重複執行的操作必須具備冪等設計

**嚴重度**：Must

**規則**
- 涉及付款、扣款、建單、發券、扣庫存、發送通知、外部系統呼叫等不可任意重複執行的操作時，必須設計冪等機制。
- 可使用 requestId、businessNo、idempotency key、唯一索引、狀態檢查或處理紀錄避免重複處理。
- 冪等 key 必須搭配資料庫唯一索引、條件更新或原子插入，不能只靠 exists-then-insert。
- 不得只依賴前端避免重複點擊。
- 重試、timeout retry、message redelivery、job rerun 都應視為可能重複執行。

**Review 重點**
- 是否有付款、扣款、發券、扣庫存、通知等操作但沒有 idempotency key。
- 是否只做 `existsByRequestId()` 後再 insert，卻沒有唯一索引或 duplicate key 處理。
- 重試或 MQ redelivery 時是否會重複產生副作用。
- 同一 requestId 再次進入時，是否能回傳原處理結果。

**原因**
- 可避免重複扣款、重複發券、重複建單、重複通知與重複庫存異動。

**反例**
```java
public PaymentResult pay(PaymentRequest request) {
    Account account = accountRepository.findById(request.getAccountId())
            .orElseThrow(() -> new AccountNotFoundException("Account not found"));

    account.setBalance(account.getBalance().subtract(request.getAmount()));
    accountRepository.save(account);

    paymentRecordRepository.save(new PaymentRecord(request.getOrderId(), request.getAmount()));
    return PaymentResult.success();
}
```

**正例**
```java
@Transactional
public PaymentResult pay(PaymentRequest request) {
    try {
        paymentRecordRepository.insertProcessing(request.getRequestId(), request.getOrderId());
    } catch (DuplicateKeyException e) {
        return paymentRecordRepository.getResultByRequestId(request.getRequestId());
    }

    Account account = accountRepository.findById(request.getAccountId())
            .orElseThrow(() -> new AccountNotFoundException("Account not found"));

    if (request.getAmount() == null || request.getAmount().compareTo(BigDecimal.ZERO) <= 0) {
        throw new BusinessException("Amount must be positive");
    }

    if (account.getBalance().compareTo(request.getAmount()) < 0) {
        paymentRecordRepository.markFailed(request.getRequestId(), "INSUFFICIENT_BALANCE");
        throw new BusinessException("Insufficient balance");
    }

    account.setBalance(account.getBalance().subtract(request.getAmount()));
    accountRepository.save(account);

    PaymentResult result = PaymentResult.success();
    paymentRecordRepository.markSuccess(request.getRequestId(), result);
    return result;
}
```

```sql
create unique index uk_payment_request_id on payment_record(request_id);
```

---

## J-7 外部系統呼叫不得破壞交易一致性

**嚴重度**：Must

**規則**
- 資料庫交易中不得隨意執行耗時、不可回滾或不受本地交易控制的外部操作。
- 常見外部操作包含 HTTP call、RPC、MQ publish、Email、SMS、檔案上傳、第三方支付或通知。
- 若必須整合外部操作，必須明確處理 timeout、retry、冪等、補償、失敗狀態與一致性邊界。
- 不得假設本地資料庫 rollback 可以回滾外部系統副作用。
- Outbox / message publish 必須具備防重處理，例如事件唯一鍵、狀態條件更新、claim 機制、外部接收方冪等 key。

**Review 重點**
- `@Transactional` 方法中是否直接呼叫 HTTP / RPC / MQ / Email / SMS client。
- 本地 DB 更新成功後，外部操作失敗時是否有狀態、補償或重試紀錄。
- 外部操作成功但本地 rollback 時是否會造成不可修復的不一致。
- Outbox consumer 是否可能被多 worker 重複發送同一事件。

**原因**
- 可避免本地交易成功但外部失敗、外部成功但本地 rollback、交易持有過久、重試造成重複副作用等問題。

**反例**
```java
@Transactional
public void createOrder(CreateOrderRequest request) {
    Order order = buildOrder(request);
    orderRepository.save(order);

    paymentClient.pay(order.getId(), order.getFinalAmount());
    notificationClient.sendOrderCreated(order.getId());

    order.setStatus(OrderStatus.PAID);
    orderRepository.save(order);
}
```

**正例**
```java
@Transactional
public void createOrder(CreateOrderRequest request) {
    Order order = buildOrder(request);
    orderRepository.save(order);

    OutboxEvent event = OutboxEvent.orderCreated(order.getId());
    outboxEventRepository.save(event);
}

public void publishPendingEvents() {
    List<OutboxEvent> events = outboxEventRepository.claimPendingEvents(100);
    for (OutboxEvent event : events) {
        try {
            notificationClient.sendOrderCreated(event.getAggregateId(), event.getEventId());
            outboxEventRepository.markPublished(event.getEventId(), OutboxStatus.PROCESSING);
        } catch (Exception e) {
            outboxEventRepository.markFailed(event.getEventId(), e.getMessage());
        }
    }
}
```

---

## J-8 重要業務異動必須保留操作紀錄

**嚴重度**：Must

**規則**
- 涉及金額、帳戶、權限、角色、重要狀態、個資、交易或設定異動時，必須保留可追蹤的操作紀錄。
- 本規則主要適用於金額、權限、個資、帳務、關鍵狀態與高風險設定異動；一般低風險 CRUD 不應在證據不足時一律推定需要正式 audit record。
- 操作紀錄至少應包含：操作者、目標資源、操作類型、異動前後關鍵狀態、操作時間、requestId / traceId。
- 不得在操作紀錄中保存完整敏感資料；必要時應脫敏或只保存摘要。
- 操作紀錄應與業務操作保持一致性，避免主資料已改但紀錄遺失。
- 稽核紀錄不應只依賴一般 application log；應使用可查詢、可保留、權限受控且格式穩定的 audit record。

**Review 重點**
- 是否修改金額、角色、權限、帳戶、交易狀態或個資，卻沒有 audit record。
- audit log 是否有操作者、目標、操作類型、時間與 requestId / traceId。
- audit log 是否保存完整敏感資料。
- 是否只用 `log.info()` 取代正式稽核紀錄。

**原因**
- 可支援稽核、問題追蹤、爭議處理、風險控管與 production incident 調查。

**反例**
```java
public void changeUserRole(Long userId, String role) {
    User user = userRepository.findById(userId)
            .orElseThrow(() -> new UserNotFoundException("User not found"));

    user.setRole(role);
    userRepository.save(user);
}
```

**正例**
```java
@Transactional
public void changeUserRole(Long userId, String newRole, LoginUser operator, String requestId) {
    User user = userRepository.findById(userId)
            .orElseThrow(() -> new UserNotFoundException("User not found"));

    String oldRole = user.getRole();
    user.setRole(newRole);
    userRepository.save(user);

    auditLogRepository.save(AuditLog.builder()
            .operatorId(operator.getUserId())
            .targetId(userId)
            .action("CHANGE_USER_ROLE")
            .beforeValue(oldRole)
            .afterValue(newRole)
            .requestId(requestId)
            .build());
}
```

---

## J-9 批次處理必須支援部分失敗、重跑與恢復

**嚴重度**：Must

**規則**
- 批次處理不得假設所有資料一次成功。
- 必須明確處理部分成功、失敗記錄、可重跑性、重複處理防護與進度追蹤。
- 不可因單筆失敗就讓整批狀態不明。
- 批次重跑時，不得重複扣款、重複發券、重複通知或重複更新已完成資料。
- 批次處理應明確定義每筆、每頁或整批的交易邊界；高風險異動通常應避免整批共用一個巨大交易。

**Review 重點**
- 批次是否一筆失敗就整批中斷且沒有失敗紀錄。
- 是否有處理狀態、checkpoint、游標、批次號或重跑條件。
- 重跑時是否會重複處理已完成資料。
- 是否把大量資料放在同一個長交易中處理。

**原因**
- 批次常會遇到單筆資料異常、外部系統 timeout、資料鎖衝突或中途停機。缺少恢復設計會造成重跑困難與資料不一致。

**反例**
```java
public void processOrders(List<Order> orders) {
    for (Order order : orders) {
        processOrder(order);
    }
}
```

**正例**
```java
public void processOrders(List<Order> orders) {
    for (Order order : orders) {
        if (OrderProcessStatus.DONE.equals(order.getProcessStatus())) {
            continue;
        }

        try {
            processOrder(order);
            order.markProcessDone();
        } catch (Exception e) {
            order.markProcessFailed(e.getMessage());
            log.error("process order failed, orderId={}", order.getId(), e);
        }

        orderRepository.save(order);
    }
}
```

---

## J-10 時間相關業務規則必須明確時區與邊界

**嚴重度**：Must

**規則**
- 涉及日期、時間區間、到期日、每日限額、帳務日、批次日切、活動期間時，必須明確指定時區與起訖邊界。
- 不得直接依賴不明確的本機預設時區或隱含的 `now`。
- 時間區間必須明確定義是否包含起點與終點，建議使用左閉右開 `[start, end)`。
- 對「今天」、「本月」、「到期日」、「交易日」、「帳務日」等詞，必須明確轉換成可驗證的時間範圍。
- DB 儲存與程式比較的時間型別必須有一致語意；不得混用本地時間、UTC 時間與業務時區時間而未明確轉換。

**Review 重點**
- 是否直接使用 `LocalDateTime.now()` 且沒有指定業務時區或 Clock。
- 是否使用 `<= endDate` 導致結束日邊界不明。
- 是否將「今天」、「本月」、「帳務日」直接當字面概念使用，未轉成明確時間範圍。
- DB 時間、API 時間、業務時區是否有混用風險。

**原因**
- 時區與邊界不明確會導致活動提前或延後結束、日限額錯算、帳務日錯誤與批次重複或漏處理。

**反例**
```java
public boolean isCampaignActive(Campaign campaign) {
    LocalDateTime now = LocalDateTime.now();
    return now.isAfter(campaign.getStartTime())
            && now.isBefore(campaign.getEndTime());
}
```

**正例**
```java
private static final ZoneId BUSINESS_ZONE = ZoneId.of("Asia/Taipei");

public boolean isCampaignActive(Campaign campaign, Clock clock) {
    ZonedDateTime now = ZonedDateTime.now(clock).withZoneSameInstant(BUSINESS_ZONE);
    ZonedDateTime start = campaign.getStartTime().atZone(BUSINESS_ZONE);
    ZonedDateTime end = campaign.getEndTime().atZone(BUSINESS_ZONE);

    return !now.isBefore(start) && now.isBefore(end);
}
```

---

## J-11 重要業務操作應避免先查後改造成併發錯誤

**嚴重度**：Must

**規則**
- 涉及庫存、餘額、額度、狀態、名額、序號等競爭資源時，不得只用「先查詢、再判斷、再更新」假設併發安全。
- 必須使用資料庫條件更新、樂觀鎖、悲觀鎖、唯一約束或其他併發控制機制。
- 更新結果必須檢查 affected rows；若更新失敗，應轉成明確業務錯誤或重試流程。
- 狀態流轉也可使用條件更新保護，例如 `where status = expectedStatus`，並檢查 affected rows。

**Review 重點**
- 是否有庫存、餘額、額度、名額等資源先查再扣。
- 是否沒有使用條件更新、version、lock 或唯一約束。
- update / delete 後是否沒有檢查 affected rows。
- 狀態更新是否缺少 `where status = ?` 之類的預期狀態條件。

**原因**
- 多個請求同時通過查詢檢查時，可能造成超賣、超扣、重複佔用、非法狀態變更等問題。

**反例**
```java
public void deductStock(Long productId, int quantity) {
    Product product = productRepository.findById(productId)
            .orElseThrow(() -> new ProductNotFoundException("Product not found"));

    if (product.getStock() < quantity) {
        throw new BusinessException("Insufficient stock");
    }

    product.setStock(product.getStock() - quantity);
    productRepository.save(product);
}
```

**正例**
```java
public void deductStock(Long productId, int quantity) {
    if (quantity <= 0) {
        throw new BusinessException("Quantity must be positive");
    }

    int updatedRows = productRepository.deductStockIfEnough(productId, quantity);
    if (updatedRows != 1) {
        throw new BusinessException("Insufficient stock");
    }
}
```

```sql
update product
set stock = stock - #{quantity}
where id = #{productId}
  and stock >= #{quantity}
```

**狀態條件更新正例**
```sql
update orders
set status = 'PAID'
where id = #{orderId}
  and status = 'CREATED'
```

---

## J-12 業務操作失敗時不得留下不明確的中間狀態

**嚴重度**：Must

**規則**
- 本規則主要適用於多步驟流程、外部副作用、非同步流程，或需要人工 / 批次續處理的狀態機。
- 多步驟業務流程必須定義清楚的成功、失敗、處理中、待補償等狀態。
- 任一步驟失敗時，必須明確更新狀態、記錄錯誤原因，或進入可重試 / 可補償流程。
- 不得讓資料停留在無法判斷下一步的半成品狀態。

**Review 重點**
- 是否在流程中先把狀態改成成功，再呼叫可能失敗的外部系統。
- 失敗後是否只 log，沒有更新失敗狀態或補償紀錄。
- 是否存在 `PROCESSING`、`FAILED`、`RETRY_PENDING`、`COMPENSATION_PENDING` 等可判斷下一步的狀態。
- job / 客服 / 人工修復是否能根據狀態判斷下一步。

**原因**
- 不明確的中間狀態會讓後續 job、客服處理、重試流程與資料修復難以判斷，容易造成重複處理或漏處理。

**反例**
```java
public void submitApplication(Long applicationId) {
    Application application = applicationRepository.findById(applicationId)
            .orElseThrow(() -> new NotFoundException("Application not found"));

    application.setStatus(ApplicationStatus.SUBMITTED);
    applicationRepository.save(application);

    riskClient.check(applicationId);
    notifyClient.sendSubmitted(applicationId);
}
```

**正例**
```java
@Transactional
public void submitApplication(Long applicationId) {
    Application application = applicationRepository.findById(applicationId)
            .orElseThrow(() -> new NotFoundException("Application not found"));

    if (!ApplicationStatus.DRAFT.equals(application.getStatus())) {
        throw new BusinessException("Only draft applications can be submitted");
    }

    application.markSubmitting();
    applicationRepository.save(application);

    applicationEventRepository.save(ApplicationEvent.riskCheckRequested(applicationId));
}

public void handleRiskCheckResult(Long applicationId, RiskResult result) {
    Application application = applicationRepository.findById(applicationId)
            .orElseThrow(() -> new NotFoundException("Application not found"));

    if (result.isPassed()) {
        application.markSubmitted();
    } else {
        application.markRiskRejected(result.getReasonCode());
    }

    applicationRepository.save(application);
}
```

---

## J-13 Request 參數必須做業務語意驗證

**嚴重度**：Must

**規則**
- Controller / service 接收到 request 後，不得只依賴型別、非空或格式驗證。
- 本規則主要適用於核心業務操作、跨資源操作，以及涉及金額、權限、狀態、時間邊界等高風險參數的情境。
- 必須檢查參數組合在業務上是否合理。
- 常見檢查包含：起訖時間順序、來源與目標不可相同、幣別是否支援、帳戶狀態是否可操作、商品 / 活動 / 優惠是否適用、通路是否允許。
- 驗證應放在清楚的 validation method、domain method 或 policy component 中，不要散落在流程中。

**Review 重點**
- 是否只有 `@NotNull`、`@Size`、`@Pattern`，但沒有業務語意驗證。
- 起日是否可能晚於迄日。
- 來源帳戶與目標帳戶是否可能相同。
- 商品、優惠、通路、帳戶狀態是否真的允許本次操作。

**原因**
- 格式合法不代表業務合法。缺少語意驗證會造成非法交易、錯用優惠、錯誤查詢範圍或不可操作資料被修改。

**反例**
```java
public void transfer(TransferRequest request) {
    accountService.transfer(request.getFromAccountId(), request.getToAccountId(), request.getAmount());
}
```

**正例**
```java
public void transfer(TransferRequest request) {
    validateTransferRequest(request);
    accountService.transfer(request.getFromAccountId(), request.getToAccountId(), request.getAmount());
}

private void validateTransferRequest(TransferRequest request) {
    if (request.getFromAccountId().equals(request.getToAccountId())) {
        throw new BusinessException("Source and target account must be different");
    }
    if (!currencyService.isSupported(request.getCurrency())) {
        throw new BusinessException("Unsupported currency");
    }
}
```

---

## J-14 核心業務不變式必須集中維護

**嚴重度**：Should

**規則**
- 核心業務物件的必要條件與衍生關係，必須集中在 domain method、factory、policy 或 service 中維護。
- 不得讓多個 API 各自手動組裝或修改同一組核心欄位。
- 若一組欄位存在固定關係，例如總金額、折扣、應付金額、狀態、明細彙總，必須由後端統一計算與校驗。
- 儲存前應確保物件不會進入違反業務不變式的狀態。

**Review 重點**
- 是否多個 API 各自計算 `totalAmount`、`discountAmount`、`finalAmount`。
- 主檔金額是否可能與明細加總不一致。
- 帳戶餘額、凍結金額、可用餘額之間是否有固定關係但未集中維護。
- entity 是否可被任意 setter 改到非法狀態。

**原因**
- 業務不變式散落會造成不同入口邏輯不一致，最後導致資料看似合法但實際違反核心業務規則。

**反例**
```java
order.setTotalAmount(request.getTotalAmount());
order.setDiscountAmount(request.getDiscountAmount());
order.setFinalAmount(request.getFinalAmount());
```

**正例**
```java
Order order = Order.create(productItems, discountPolicy);
order.validateBeforeSave();
orderRepository.save(order);
```

---

## J-15 退款、撤銷與補償操作必須綁定原始交易

**嚴重度**：Must

**規則**
- 退款、撤銷、沖正、取消、補償、回補庫存、退點、退券等反向操作，必須以原始交易或原始業務紀錄為基準。
- 不得直接信任 request 傳入的退款金額、回補數量、原狀態或補償結果。
- 必須檢查原交易是否存在、是否屬於可反向操作狀態、是否已部分或全部處理過。
- 反向操作金額或數量不得超過原交易剩餘可處理範圍。
- 補償流程本身也必須具備冪等性與操作紀錄。

**Review 重點**
- 退款金額是否直接來自 request，而不是原交易與已退款紀錄計算。
- 取消訂單是否檢查原訂單狀態。
- 回補庫存、退點、退券是否可能重複執行。
- 是否有 reversal / refund / compensation record 綁定原交易單號。

**原因**
- 反向操作若未綁定原交易，容易造成超退、重複補償、資料對不上與帳務不一致。

**反例**
```java
public void refund(RefundRequest request) {
    refundService.refund(request.getOrderId(), request.getRefundAmount());
}
```

**正例**
```java
public void refund(RefundRequest request) {
    Order order = orderRepository.findById(request.getOrderId())
            .orElseThrow(() -> new OrderNotFoundException("Order not found"));

    if (!order.canRefund()) {
        throw new BusinessException("Order cannot be refunded");
    }

    BigDecimal refundableAmount = refundRepository.calculateRefundableAmount(order.getId());
    if (request.getRefundAmount().compareTo(refundableAmount) > 0) {
        throw new BusinessException("Refund amount exceeds refundable amount");
    }

    refundRepository.createRefundRecord(order.getId(), request.getRequestId(), request.getRefundAmount());
}
```

---

## J-16 多資料表異動必須定義一致性邊界

**嚴重度**：Must

**規則**
- 同一個業務操作若會異動多個本地資料表，必須明確定義交易邊界。
- 主檔、明細、異動紀錄、餘額、庫存、狀態等資料若需要一起成功或一起失敗，必須放在同一個本地交易內。
- 若因架構限制無法放在同一交易，必須設計可重試、可補償、可對帳的狀態與紀錄。
- 不得讓主資料成功但明細、紀錄或彙總資料遺失。

**Review 重點**
- 是否先存主檔，後存明細，但沒有交易保護。
- 帳戶餘額與交易紀錄是否可能一個成功、一個失敗。
- 優惠券狀態與使用紀錄是否可能不一致。
- 本地多表異動是否被拆成多個沒有一致性設計的方法。

**原因**
- 多表資料若缺乏一致性邊界，容易出現主從資料不一致、帳務紀錄缺失、狀態與明細對不上等 production 問題。

**反例**
```java
public void createOrder(Order order, List<OrderItem> items) {
    orderRepository.save(order);
    orderItemRepository.saveAll(items);
    auditLogRepository.save(AuditLog.orderCreated(order.getId()));
}
```

**正例**
```java
@Transactional
public void createOrder(Order order, List<OrderItem> items) {
    orderRepository.save(order);
    orderItemRepository.saveAll(items);
    auditLogRepository.save(AuditLog.orderCreated(order.getId()));
}
```

---

## J-17 涉及外部系統或帳務結果的流程必須可對帳

**嚴重度**：Must（涉及金額、帳務、支付、點數、券、交易時）；其他外部整合場景為 Should

**規則**
- 涉及付款、扣款、退款、點數、券、庫存、外部訂單、MQ 或批次交換的流程，必須保留可對帳資料。
- 對帳資料至少應包含本地業務單號、外部系統單號、金額 / 數量、狀態、處理時間、requestId / traceId。
- 不得只依賴單次 API 回應作為最終真相。
- 若本地與外部狀態不一致，必須有明確的人工處理、重試或補償流程。

**Review 重點**
- 是否有外部支付、退款、點數、券、MQ 或批次交換，但沒有保存外部單號。
- 是否只有同步 API response，沒有可查詢的本地處理紀錄。
- 是否缺少對帳狀態、差異狀態或人工處理入口。
- 異常時是否能從資料判斷本地與外部各自的最終狀態。

**原因**
- 外部系統與本地資料無法永遠靠單次同步呼叫保持一致。可對帳資料能支援補償、稽核、客服查詢與 production incident 修復。

**反例**
```java
PaymentResponse response = paymentClient.pay(request);
if (response.isSuccess()) {
    order.markPaid();
}
```

**正例**
```java
PaymentRecord record = PaymentRecord.builder()
        .orderId(order.getId())
        .requestId(request.getRequestId())
        .localAmount(order.getFinalAmount())
        .externalPaymentNo(response.getPaymentNo())
        .status(response.isSuccess() ? PaymentStatus.SUCCESS : PaymentStatus.FAILED)
        .build();
paymentRecordRepository.save(record);
```

---

## J-18 業務錯誤必須可分類且語意穩定

**嚴重度**：Must（對外 API、批次、上游系統依賴錯誤結果時）；其他內部低風險流程為 Should

**規則**
- 業務規則不通過時，應回傳穩定的業務錯誤碼或明確例外類型。
- 不得把可預期的業務失敗全部包成系統錯誤。
- 常見業務錯誤包含：資料不存在、無權操作、狀態不可轉換、餘額不足、庫存不足、超過限制、重複提交。
- 錯誤訊息不得洩漏敏感資料或內部技術細節。
- 錯誤碼應能支援前端提示、客服查詢、批次判斷與監控分類。

**Review 重點**
- 是否所有錯誤都丟 `RuntimeException` 或回 `INTERNAL_ERROR`。
- 餘額不足、庫存不足、狀態不可操作等可預期錯誤是否有穩定錯誤碼。
- 錯誤訊息是否暴露 SQL、class name、stack trace、完整個資或內部系統資訊。
- 批次或上游系統是否能根據錯誤類型決定重試、跳過或人工處理。

**原因**
- 穩定錯誤分類能降低前端、客服、批次、監控與上游系統的整合成本，也能避免把正常業務失敗誤判成系統異常。

**反例**
```java
if (account.getBalance().compareTo(amount) < 0) {
    throw new RuntimeException("balance not enough, account=" + account);
}
```

**正例**
```java
if (account.getBalance().compareTo(amount) < 0) {
    throw new BusinessException("INSUFFICIENT_BALANCE", "Insufficient balance");
}
```

---

# K 區：Tests & Review Coverage

> 目的：確保重要 Java 業務邏輯可被驗證，不只依賴人工推論或 happy path 測試。

---

## K-1 核心業務邏輯必須有對應測試

**嚴重度**：Must

**規則**
- 當本次變更涉及金額、狀態流轉、權限、冪等、批次、外部系統、時間邊界、併發控制、退款 / 補償、多表一致性等核心邏輯時，必須有單元測試、整合測試或可執行的驗證方式。
- 不得只依賴手動測試或口頭確認。
- 若修改的是既有核心流程，review 時應確認是否同步新增或調整測試。

**Review 重點**
- PR 是否只改 production code，沒有任何測試或驗證說明。
- 金額、狀態、冪等、授權、時間、併發條件是否有測試覆蓋。
- 測試是否能在 CI 或本地穩定執行。

**原因**
- 核心業務邏輯沒有測試時，後續重構、需求變更與 bug fix 容易破壞既有規則。

---

## K-2 測試不得只覆蓋 happy path

**嚴重度**：Must

**規則**
- 本規則主要在 K-1 已觸發時強制適用，不要求所有低風險變更都同時補齊完整邊界案例。
- 測試必須覆蓋正常、異常與邊界案例。
- 常見必要案例包含：`null`、空集合、資料不存在、無權限、非法狀態、重複 requestId、金額為 0、金額為負、超過餘額、庫存不足、時間等於起點 / 終點、外部系統失敗。
- 對狀態流轉，至少應測試允許轉移與不允許轉移。
- 對金額計算，至少應測試 scale、rounding、邊界金額與不同幣別 / 單位禁止混算。

**Review 重點**
- 測試是否只驗證成功流程。
- 是否缺少邊界值與失敗情境。
- 測試名稱是否清楚描述情境與預期結果。

**原因**
- Production 問題多數發生在例外、邊界、重試、併發與資料異常場景，而不是 happy path。

---

## K-3 外部系統整合必須測試 timeout、retry、重複回調與失敗補償

**嚴重度**：Must

**規則**
- 當本次變更涉及 HTTP、RPC、MQ、Email、SMS、第三方支付、檔案交換等外部系統流程或其失敗處理時，測試不得只驗證成功回應。
- 必須測試 timeout、失敗、重試、重複訊息、重複 callback、外部成功但本地失敗、本地成功但外部失敗等情境。
- 若使用 outbox、補償或對帳流程，應測試狀態轉換與重跑結果。

**Review 重點**
- 是否 mock 外部 client 並覆蓋失敗路徑。
- 重試是否會造成重複副作用。
- 重複 callback 或 MQ redelivery 是否會保持冪等。

**原因**
- 外部系統整合的風險通常來自非同步、timeout、重試與不一致，而不是單次成功呼叫。

---

## K-4 測試資料應清楚且避免脆弱依賴

**嚴重度**：Should

**規則**
- 測試資料應能清楚表達業務情境，不要使用無語意的 `test1`、`123`、`foo` 填滿核心欄位。
- 測試不得依賴執行順序、當前系統時間、外部網路、共享資料庫殘留狀態或不穩定隨機值。
- 時間相關測試應注入 `Clock` 或固定時間來源。
- 隨機資料若會影響斷言，必須固定 seed 或改用明確資料。

**Review 重點**
- 測試是否 flaky。
- 是否依賴 `LocalDateTime.now()`、外部 API 或資料庫既有資料。
- 測試資料是否讓人看得出業務意義。

**原因**
- 脆弱測試會降低團隊對測試的信任，也會讓 CI 結果失去判斷價值。

---

# L 區：Spring / Framework / Transaction Usage

> 目的：補強 Java / Spring backend 常見框架使用風險，避免交易失效、Controller 過重、DTO / Entity 邊界混亂與框架隱性行為造成 production 問題。

---

## L-1 `@Transactional` 必須放在正確交易邊界

**嚴重度**：Must

**規則**
- `@Transactional` 應放在明確的 service 層交易邊界，不應依賴 private method 或 self-invocation 觸發交易。
- 不得在同一交易中隨意包住耗時或不可回滾的外部操作，例如 HTTP、RPC、MQ publish、Email、SMS、第三方支付。
- 修改多個本地資料表且需要一起成功 / 失敗時，必須明確定義 transaction boundary。
- 若方法丟出 checked exception 且需要 rollback，必須明確設定 rollback rule 或轉成適當的 runtime exception。
- 查詢流程若不需要寫入，可視情境使用 `@Transactional(readOnly = true)`。

**Review 重點**
- `@Transactional` 是否標在 private method 或同類內部呼叫的方法上。
- 交易內是否直接呼叫外部系統。
- checked exception 是否可能導致沒有 rollback。
- 多表異動是否缺少交易保護。

**原因**
- Spring transaction 依賴 proxy 行為；錯誤使用會讓交易沒有生效，或造成交易持有過久與外部副作用不可回滾。

---

## L-2 Controller 不應承載核心業務邏輯

**嚴重度**：Major

**規則**
- Controller 應主要負責 request 接收、登入者上下文取得、基本參數轉換、呼叫 service 與組裝 response。
- Controller 不應直接承載金額計算、狀態流轉、權限細節、多表資料異動、外部系統 orchestration 或複雜業務判斷。
- 若 Controller 內出現大量 if / else、DB 操作、交易註解或核心 domain rule，應移入 service、domain method 或 policy component。

**Review 重點**
- Controller 是否直接呼叫 repository / mapper。
- Controller 是否計算 finalAmount、改狀態、判斷權限或操作多表。
- 多個 Controller 是否重複實作相同業務規則。

**原因**
- Controller 過重會讓業務規則分散，降低可測試性與一致性，也容易造成不同入口行為不一致。

---

## L-3 Request DTO、Response DTO 與 Entity 不得混用

**嚴重度**：Major

**規則**
- API request 不應直接使用 Entity 接收。
- API response 不應直接回傳 Entity。
- Request DTO 應只包含使用者可輸入的欄位，不應包含後端計算結果、權限、狀態、餘額等敏感或結果型欄位。
- Response DTO 應以 API contract 與最小化輸出為準，不應暴露內部資料表結構、lazy loading 關聯或敏感欄位。
- DTO 與 Entity 的轉換應明確，不得依賴隱性 side effect。

**Review 重點**
- Controller 是否使用 Entity 作為 `@RequestBody` 或直接 return Entity。
- Response 是否可能因 Jackson 自動序列化暴露敏感欄位或 lazy loading 關聯。
- Request DTO 是否包含 `role`、`status`、`balance`、`finalAmount` 等不應由前端決定的欄位。

**原因**
- DTO / Entity 混用會造成資安外洩、API contract 不穩、資料表結構外露與 request 欄位被竄改的風險。

---

## L-4 Bean 生命週期與 singleton 狀態必須安全

**嚴重度**：Major

**規則**
- Spring singleton bean 中不得保存 request-specific mutable state，例如目前使用者、當前訂單、暫存金額、處理中資料。
- 若需要跨方法傳遞狀態，應使用方法參數、區域變數、明確 context object 或受控的 request scope。
- 若使用 cache、map、list 等成員變數，必須確認 thread-safety、生命週期、清理策略與容量限制。

**Review 重點**
- Service 是否有可變成員欄位保存單次請求資料。
- Singleton bean 是否使用非 thread-safe collection 承載共享資料。
- 是否有資料跨請求污染風險。

**原因**
- Spring service 預設通常是 singleton，多執行緒同時呼叫時，共用可變狀態會導致資料污染與競態。

---

## L-5 框架自動綁定與序列化不得繞過安全邊界

**嚴重度**：Major

**規則**
- 不得因 Jackson、BeanUtils、ModelMapper、MapStruct 或其他自動 mapping 工具方便，就無差別複製所有欄位。
- 從 request 複製到 Entity 時，必須明確排除不可由使用者修改的欄位，例如 id、ownerId、tenantId、role、status、balance、createdAt、updatedBy。
- 序列化輸出前必須確認敏感欄位、內部欄位與關聯物件不會被自動輸出。

**Review 重點**
- 是否使用 `BeanUtils.copyProperties(request, entity)` 直接覆蓋 Entity。
- 是否缺少欄位白名單。
- 是否可能 mass assignment，讓使用者修改不該修改的欄位。

**原因**
- 自動 mapping 很容易引入 mass assignment、敏感欄位外洩與資料誤覆蓋。

---

# M 區：Cache & Distributed Safety

> 目的：補強 Java backend 使用 Redis、local cache、分散式鎖或多 instance 部署時的資料一致性與安全風險。

---

## M-1 Cache key 必須包含足夠業務維度

**嚴重度**：Major

**規則**
- Cache key 必須包含足以區分資料歸屬與查詢條件的維度，例如 tenantId、userId、accountId、locale、currency、permission scope、query condition。
- 不得只用容易碰撞或跨租戶混淆的 key，例如單純 `user:{id}`，卻忽略 tenant / branch / environment。
- Cache key 的組成規則應集中管理，避免各處手寫不一致。
- 只有在 diff 或上下文可明確看出 cache key 組成與查詢維度時，才應作為正式 finding；若證據不足，優先列為開放問題。

**Review 重點**
- cache key 是否缺少 tenantId / userId / permission scope。
- 不同查詢條件是否可能共用同一 key。
- 是否有跨使用者或跨租戶讀到錯誤資料的風險。

**原因**
- Cache key 維度不足會導致資料污染、越權讀取與難以追查的一致性問題。

---

## M-2 DB 更新後必須處理 cache 一致性

**嚴重度**：Major

**規則**
- 若資料同時存在 DB 與 cache，更新 DB 後必須明確處理 cache 失效、更新或延遲雙刪等一致性策略。
- 不得只更新 DB 而忽略 cache。
- 若 cache 內容影響權限、餘額、庫存、狀態或敏感資料，應視為高風險。
- Cache 失效失敗時，應有重試、補償、短 TTL 或其他風險降低措施。

**Review 重點**
- 修改資料後是否刪除或更新相關 cache。
- cache 是否可能長時間保留舊狀態、舊權限或舊餘額。
- cache 操作失敗是否只 log 後忽略。

**原因**
- DB 與 cache 不一致可能造成讀到舊資料、錯誤權限、錯誤金額或錯誤狀態。

---

## M-3 分散式鎖不得作為唯一正確性保證

**嚴重度**：Major

**規則**
- 分散式鎖可以降低併發衝突，但不得取代資料庫唯一索引、條件更新、樂觀鎖或業務冪等設計。
- lock key 必須包含正確業務維度，避免鎖太粗造成效能問題，或鎖太細造成保護失效。
- lock 必須有合理 TTL，並處理取得鎖失敗、執行逾時與釋放鎖失敗情境。
- 不得在未確認鎖 ownership 的情況下釋放別人的鎖。

**Review 重點**
- 是否只靠 Redis lock 防止重複扣款 / 扣庫存，沒有 DB 條件保護。
- lock key 是否缺少 orderId / accountId / tenantId 等維度。
- 是否有 finally 釋放鎖，但沒有確認 owner token。

**原因**
- 分散式鎖在 timeout、網路抖動、process pause、重試時可能失效，核心資料正確性仍應由 DB 約束與冪等設計保護。

---

## M-4 Cache 中不得存放未保護的敏感資料

**嚴重度**：Must

**規則**
- Cache 中不得存放不必要的完整敏感資料，例如完整卡號、Token、密碼、憑證、金鑰、完整身分證字號或完整個資。
- 必須存放時，應確認最小化、脫敏、TTL、存取權限、加密與清除策略。
- 不得把完整 request / response / entity 無差別塞入 cache。

**Review 重點**
- cache value 是否包含完整敏感資料。
- 是否有 TTL 與清除策略。
- 是否能避免不同使用者或服務讀到不該讀的 cache 資料。

**原因**
- Cache 常被多服務共用且保留時間較長，一旦外洩或 key 設計錯誤，敏感資料風險會被放大。

---

---

# 最終收斂原則

> 若遇到本文件未明確定義的情境，優先採用風險最低、型別安全、可讀性較高，且不引入隱性行為或 magic side-effect 的寫法。  
> 若業務規則、資料歸屬、交易邊界、狀態流轉、外部一致性、快取一致性或測試覆蓋不明確，review 時應優先視為高風險，要求補上明確設計、檢查條件、狀態紀錄、測試或補償流程。
