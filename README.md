# 品質管理系統（QMS）MVP

Quality management system repository。此專案延續既定規劃：PC Django 管理後台、Android App 透過 REST API 操作，以及 MySQL/MariaDB 資料庫。第一版先落地產品、檢驗項目、批次、檢驗結果與不良品改善流程。

## 已建立

- 自訂使用者與角色（管理員、品質主管、檢驗人員）
- 產品分類、產品、檢驗項目，以及產品與檢驗項目的多對多設定
- 檢驗批次、檢驗紀錄與逐項檢驗結果
- 不良類型、不良紀錄、照片、改善措施
- Django Admin 與基本儀表板
- Android 可使用的 API：待檢驗批次、產品檢驗項目、提交檢驗結果

## 本機啟動

需要 Python 3.12+ 與 MySQL/MariaDB（或預設 SQLite）。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py makemigrations accounts products inspections defects
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

開啟 `http://127.0.0.1:8000/admin/` 先設定角色、產品、檢驗項目與批次；登入後根網址為儀表板。

## 測試資料

套用 migration 後，可建立基本測試資料：

```powershell
python manage.py seed_demo_data
```

包含 3 個角色、1 個產品分類、3 個產品、2 個檢驗項目、8 個批次、4 筆檢驗紀錄、8 筆檢驗結果、1 個不良類型、3 筆不良紀錄及 2 筆改善措施。批次涵蓋待檢驗、檢驗中、合格與不合格情境，檢驗結果包含標準快照；不會建立假照片。

示範資料以 `DEMO-` 或 `DEMO -` 前綴識別。指令可重複執行，不覆寫既有資料或重新建立既有批次的紀錄。新建的 `demo_inspector` 具有 `INSPECTOR` 角色，但沒有可登入的密碼；需要測試 API 登入時，請在終端機執行 `python manage.py changepassword demo_inspector` 設定密碼。既有同名帳號的密碼與權限不會被修改。管理後台請使用自行建立的管理員帳號。

## 語系與雙語切換

- 預設語言為繁體中文（`zh-hant`），並提供 English 切換。
- 儀表板右上角提供語言切換按鈕，會使用 Django `set_language` 以 **POST + CSRF 保護** 更新 `django_language` cookie，並導回目前頁面。
- Django Admin 會沿用相同的語言 cookie，因此從儀表板切換後再進入 Admin，模型名稱、欄位名稱與 choices 會同步顯示對應語言。
- 專案翻譯檔位於 `locale/zh_Hant/LC_MESSAGES/` 與 `locale/en/LC_MESSAGES/`。

### 翻譯檔編譯

本 repository 已提交可直接執行的 `.mo` 檔，因此即使本機沒有 gettext / `msgfmt` 工具也能直接運作。

若環境已安裝 gettext，可在修改 `.po` 後執行：

```powershell
django-admin compilemessages
```

## MySQL 設定

請設定環境變數後執行 migration：

```powershell
$env:DB_ENGINE='mysql'
$env:DB_NAME='qms_db'
$env:DB_USER='root'
$env:DB_PASSWORD='your-password'
$env:DB_HOST='127.0.0.1'
$env:DB_PORT='3306'
python manage.py migrate
```

不建議先執行舊版手寫 `CREATE TABLE`，因為本專案採 Django migration 管理資料表，兩者混用會造成資料表衝突。

## API

角色、群組及後台存取規則請見 [權限設定](docs/permissions.md)。新增或升級環境後，請執行 `python manage.py sync_role_permissions` 同步既有帳號。

所有 API 需要已登入、啟用中的使用者，並檢查角色與對應操作權限；超級使用者不需要另設角色。

- `GET /api/inspection/pending/`
- `GET /api/products/{product_id}/inspection-items/`
- `POST /api/inspection/batches/{batch_id}/start/`
- `POST /api/inspection/batches/{batch_id}/release/`
- `POST /api/inspection/submit/`

提交範例：

```json
{
  "batch_id": 1,
  "remark": "首件檢驗",
  "results": [
    {
      "product_item_id": 1,
      "measured_value": 5.10,
      "result": "PASS"
    }
  ]
}
```

`product_item_id` 請先透過 `GET /api/products/{product_id}/inspection-items/` 取得；該 API 會同時回傳 `item_id` 供顯示/對照使用，但提交時必須使用 `product_item_id`。系統會驗證所有 `is_required=true` 的項目是否完整提交，並在建立檢驗結果時保存當下檢驗標準快照。

開始檢驗會將批次標為 `INSPECTING` 並記錄負責人，同一人可重複開始以續作。負責人可釋放回 `PENDING`；管理員、品質主管及超級使用者可釋放他人的批次。普通檢驗員的待檢清單只包含未指派或自己的批次。舊有未指派的檢驗中批次可以認領；直接提交未指派批次仍相容，並在交易內認領。已完成或取消的批次不可開始、釋放或重複提交。

有數值上下限的有效項目必須提供量測值，範圍含上下界；超規不能提交為 PASS。範圍內仍可因其他異常人工標為 FAIL。選填項目可省略或使用 NA，但空白或全 NA 的檢驗不可提交。

每個 FAIL 項目會自動建立一筆 `NEW` 不良紀錄，暫用 `Inspection failure` 類型，保存項目、量測值、規格及備註。回應包含 `defect_ids`；後續分類、圖片與改善措施請在管理後台處理。檢驗紀錄、結果、不良紀錄及批次完成狀態在同一交易內寫入，任一失敗會全部回滾。進一步流程說明見 [docs/workflows.md](docs/workflows.md)。

## Android Studio / Android App

- Android Studio 專案位於 `android-app/`
- 可直接在 Android Studio 開啟 `android-app` 資料夾
- 首版已包含登入、待檢驗批次、檢驗項目、檢驗結果填寫四個核心畫面
