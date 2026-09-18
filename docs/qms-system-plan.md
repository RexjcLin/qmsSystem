# QMS 品質管理系統規劃

## 1. 系統定位

QMS（Quality Management System）用於管理產品、檢驗標準、檢驗批次、檢驗結果、不良品與改善措施，建立可追溯的品質流程。

核心流程：

```text
產品管理 → 設定檢驗標準 → 建立檢驗批次 → 執行檢驗
→ 判定結果 → 建立不良品 → 指派改善措施 → 追蹤結案
```

## 2. 技術架構

- 資料庫：MySQL 8
- 資料庫名稱：`qms_db`
- 字元集：`utf8mb4`
- 後端：Django + Django REST Framework
- 驗證：Django 使用者模型與 JWT
- Web：PC 管理後台
- 行動端：Android Kotlin App（API 穩定後開發）
- 檔案：Django Media Storage；資料庫只保存檔案路徑

正式資料庫結構以 Django Migrations 為來源，不直接以手寫 SQL 取代 Migration。

## 3. MVP 範圍

### 3.1 使用者與權限

- 使用者登入、登出與密碼雜湊
- ADMIN、QUALITY_MANAGER、INSPECTOR 三種角色
- 依角色限制產品、檢驗、缺失與改善措施操作權限
- 記錄重要資料的建立者、負責人與修改歷程

### 3.2 基礎資料

- 產品分類管理
- 產品管理
- 可重複使用的檢驗項目
- 產品與檢驗項目的多對多設定
- 檢驗類型：數值、文字、布林、PASS/FAIL、選項
- 不良類型管理

### 3.3 檢驗作業

- 建立檢驗批次
- 指派檢驗人員
- 建立檢驗紀錄
- 輸入各檢驗項目結果
- 自動計算整體 PASS/FAIL/PENDING
- 管理批次狀態：PENDING、INSPECTING、COMPLETED、CANCELLED

### 3.4 不良品與改善

- 建立不良品紀錄
- 上傳不良品圖片
- 管理不良品狀態：NEW、CONFIRMED、PROCESSING、RESOLVED、CLOSED
- 建立、指派與追蹤改善措施
- 管理改善期限與完成時間

## 4. 重要設計原則

### 4.1 保存檢驗標準快照

`inspection_results` 應關聯 `product_inspection_items`，而不是只關聯通用的 `inspection_items`。儲存結果時，另外保存當次使用的檢驗方法、標準上下限與標準值快照，確保日後標準異動不會影響歷史資料的正確性。

### 4.2 使用 Django 原生帳號機制

不自行實作密碼驗證與雜湊。使用 Django `AbstractUser`、`Group`、`Permission` 及既有 authentication framework。

### 4.3 建立稽核紀錄

重要異動應記錄使用者、操作、資料表、資料識別碼、異動前資料、異動後資料與時間，滿足品質追溯需求。

## 5. 專案結構

```text
qmsSystem/
├── README.md
├── .env.example
├── requirements.txt
├── manage.py
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/
│   ├── products/
│   ├── inspections/
│   ├── defects/
│   ├── corrective_actions/
│   ├── audit_logs/
│   └── reports/
├── database/
│   └── seed_data/
├── docs/
├── media/
└── tests/
```

## 6. 開發階段

1. **基礎建置**：Django、MySQL、環境變數、自訂使用者、JWT、權限。
2. **基礎資料**：產品分類、產品、檢驗項目、檢驗標準、不良類型。
3. **檢驗流程**：批次、檢驗紀錄、結果輸入、自動判定、狀態流轉。
4. **不良與改善**：缺失、圖片、改善措施、期限提醒與結案。
5. **Web 與報表**：後台、檢驗頁、看板、合格率與不良率。
6. **Android App**：批次查詢、行動檢驗、拍照、離線暫存與同步。

## 7. 驗收標準

- 可登入並依角色使用功能
- 可建立產品與產品檢驗標準
- 可建立批次並完成一筆完整檢驗
- 檢驗結果可保存當時標準快照
- FAIL 結果可建立不良品與圖片
- 不良品可指派改善措施並追蹤狀態
- 重要異動具備稽核紀錄
- API 與資料庫測試可重複執行
