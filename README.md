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

所有 API 預設需要已登入的使用者。

- `GET /api/inspection/pending/`
- `GET /api/products/{product_id}/inspection-items/`
- `POST /api/inspection/submit/`

提交範例：

```json
{"batch_id": 1, "remark": "首件檢驗", "results": [{"item_id": 1, "measured_value": 5.10, "result": "PASS"}]}
```


## Android Studio / Android App

- Android Studio 專案位於 `android-app/`
- 可直接在 Android Studio 開啟 `android-app` 資料夾
- 首版已包含登入、待檢驗批次、檢驗項目、檢驗結果填寫四個核心畫面
