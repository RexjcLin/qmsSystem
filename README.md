# 品質管理系統（QMS）資料層

此專案依 `docs/qms-system-plan.md`、`docs/erd.md` 與 `docs/workflows.md` 實作 QMS 初始 Django 資料層，包含自訂使用者、產品與檢驗設定、檢驗紀錄、不良品、改善措施、稽核紀錄、管理後台、seed data 與模型測試。

## 已包含的 Django apps

- `accounts`
- `products`
- `inspections`
- `defects`
- `corrective_actions`
- `audit_logs`

## 環境需求

- Python 3.12+
- MySQL 8 / MariaDB（正式建議）
- 或預設 SQLite（本機快速啟動）

## 安裝與設定

1. 建立虛擬環境並安裝套件：

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. 複製環境變數範例（供 shell / IDE / direnv 載入參考）：

   ```bash
   cp .env.example .env
   ```

3. 依需求建立 MySQL 資料庫：

   ```sql
   CREATE DATABASE qms_db
     CHARACTER SET utf8mb4
     COLLATE utf8mb4_unicode_ci;
   ```

4. 設定環境變數後執行 migration：

   ```bash
   export DJANGO_SECRET_KEY="replace-me"
   export DJANGO_DEBUG=1
   export DB_ENGINE=mysql
   export DB_NAME=qms_db
   export DB_USER=root
   export DB_PASSWORD=change-me
   export DB_HOST=127.0.0.1
   export DB_PORT=3306
   python manage.py migrate
   ```

   若未設定 `DB_ENGINE=mysql`，專案會使用 SQLite 作為本機開發預設值。

## Seed data

執行下列命令會以可重複執行的方式建立角色、代表帳號、產品分類、產品、檢驗項目、產品檢驗設定與不良類型：

```bash
python manage.py seed_qms_data
```

代表帳號密碼應透過環境變數提供，例如：

```bash
export QMS_ADMIN_PASSWORD="ChangeMeAdmin123!"
export QMS_MANAGER_PASSWORD="ChangeMeManager123!"
export QMS_INSPECTOR_PASSWORD="ChangeMeInspector123!"
python manage.py seed_qms_data
```

若未提供上述環境變數，seed command 會使用僅供本機開發的預設密碼。請勿在正式環境沿用。

## 管理後台與 API

```bash
python manage.py createsuperuser
python manage.py runserver
```

- Admin: `http://127.0.0.1:8000/admin/`
- API:
  - `GET /api/inspection/pending/`
  - `GET /api/products/{product_id}/inspection-items/`
  - `POST /api/inspection/submit/`

JWT 已啟用於 DRF authentication 設定，可在後續 API 擴充登入/刷新端點。

## 測試

```bash
python manage.py test
```

目前測試涵蓋：

- 產品檢驗設定唯一鍵
- 檢驗結果快照行為
- 主要狀態預設值
- 重要刪除/保護關係
