# java-code-rules.md

> 目的：給在產生 Java 程式前必須先閱讀的機械式規則。  
> 原則：以下規則以可執行、低歧義、可穩定套用為優先。
>
> 說明：
> - 本文件為 AI coding agent 在產生 Java 程式碼前必須遵守的硬性規則。
> - 規則優先於個人偏好、框架預設行為與臨時寫法。
> - 若遇到規則衝突，以「避免風險 > 可讀性 > 簡潔性」為優先順序。
> - 本文件主要適用於正式業務程式碼（production / core logic）；一次性 migration、POC、教學範例除非有明確要求，否則可視情境放寬。

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

## B-13 `equals` 比較應由常量或保證非 null 的對象發起

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

## B-14 包裝型別比較內容不可用 `==`

**規則**
- `Integer`、`Long`、`Boolean` 等包裝型別比較內容時，一律使用 `equals()`。
- 不要用 `==` 比較包裝型別的值。

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
if (a.equals(b)) {
    System.out.println("equal");
}
```

---

## B-15 覆寫 `equals()` 時必須同步覆寫 `hashCode()`

**規則**
- 只要覆寫 `equals()`，就必須同步覆寫 `hashCode()`。
- 若類型會作為 `Map` key、`Set` 元素、去重依據或快取 key，更要確保兩者依據相同欄位。

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

## B-16 相同商業意義的方法命名應一致

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

## B-17 方法應盡量只處理一件事，並保持低耦合

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

## C-18 不要在 `foreach` 中直接增刪集合元素

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

## C-19 `Arrays.asList()` 的結果不可做 `add/remove/clear`

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

## C-20 集合轉陣列時使用 `toArray(T[] array)` 的安全寫法

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

## C-21 泛型不要省略型別資訊

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

## D-23 建立執行緒池不要用 `Executors`，改用 `ThreadPoolExecutor`

**規則**
- 禁止使用 `Executors.newFixedThreadPool()`、`newCachedThreadPool()`、`newSingleThreadExecutor()`、`newScheduledThreadPool()` 直接建立執行緒池。
- 必須使用 `ThreadPoolExecutor` 顯式設定執行緒數、佇列容量與拒絕策略。
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

## D-24 `ThreadLocal` 使用完必須 `remove()`

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

## D-25 共用可變狀態要避免競態，必要時選對同步或並發容器

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

## D-26 不要在沒有邊界與監控下隨意建立執行緒

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

## E-27 例外不可吞掉；不處理就往上拋

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

## E-28 最上層例外處理要轉成可理解、可追蹤的結果

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

## E-29 優先使用 try-with-resources 管理可關閉資源

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

## E-30 `finally` 區塊中禁止 `return`

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

## E-31 `finally` 中不要再丟新例外或覆蓋原錯誤

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

## E-32 主動防範 NPE，特別注意高風險缺值來源

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

## E-33 `Optional` 可用於表達可能缺值的回傳，但不要濫用

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

## F-34 日誌統一透過 SLF4J

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

## F-35 / F-36 記錄例外時，要同時留下原始例外物件與足夠業務上下文

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

## F-37 避免在高頻路徑做大量無條件字串拼接日誌

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

## G-38 有唯一性要求的資料，資料庫層必須建立唯一索引

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

## G-39 JOIN 欄位型別必須一致，且要有索引

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

## G-40 單條 SQL 不得超過三表 JOIN

**規則**
- 單條 SQL 不得設計超過三表 JOIN。
- 若業務需求需要跨更多資料實體，應優先考慮拆查詢、調整資料模型、增加冗餘欄位、快取或其他更可維護的方案。
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

## G-41 分頁查詢中禁止使用前置萬用字元 `LIKE`

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

## G-42 ORM / SQL 參數綁定不可用 `${}` 取代 `#{}`

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

## G-43 不要把查詢結果直接映成 `HashMap/HashTable`

**規則**
- ORM / DAO 查詢結果不得默認使用 `HashMap` / `HashTable` 等鬆散結構承載。
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

## G-44 禁止設計通用全欄位更新

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

## G-45 SQL / ORM 設計要偏向明確欄位、明確模型、明確映射

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
> 收斂原則：若遇到本文件未明確定義的情境，優先採用風險最低、型別安全、可讀性較高，且不引入隱性行為或 magic side-effect 的寫法。