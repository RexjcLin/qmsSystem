# QMS 工作流程

## 目前檢驗流程實作

手機端以 Basic Auth 驗證，讀取產品項目關聯 ID 後開始或續作批次；同一人可重入，其他人不可接手。負責人可釋放自己的批次，主管可釋放他人的批次。開始及釋放由 API 行鎖交易保護，提交時再次檢查負責人、狀態、項目與規格。預設 SQLite 的鎖定能力不同於 MySQL，正式多人併發驗收應使用正式資料庫測試。

數值項目需要量測值，超規 PASS 會被拒絕；範圍內可因其他異常人工選 FAIL。任一已提交項目 FAIL（包含選填項目）即使整體 FAIL。必填不可 NA，不接受空白或全 NA；快照以提交時的標準為準。

每個 FAIL 自動建立 NEW 缺陷，與檢驗結果及批次完成狀態在同一交易內保存。後續照片、缺陷分類調整與改善措施在 Django 後台完成；手機缺陷編輯／照片上傳、草稿持久保存及完整稽核流程尚未實作。下列流程亦包含後續規劃，並非每項規則均已有程式驗證。

## 1. 角色與責任

| 角色 | 主要責任 |
|---|---|
| ADMIN | 使用者、角色、系統設定與基礎資料管理 |
| QUALITY_MANAGER | 檢驗標準審核、品質判定、不良與改善追蹤、報表 |
| INSPECTOR | 執行檢驗、輸入結果、回報不良與上傳圖片 |

## 2. 產品與檢驗標準流程

```text
建立產品分類
  ↓
建立產品（產品代碼、名稱、規格）
  ↓
選擇可重複使用的檢驗項目
  ↓
設定檢驗類型、標準值、上下限、是否必填與順序
  ↓
儲存產品檢驗標準
```

規則：

- 已被歷史檢驗使用的標準不應直接覆蓋而失去版本資訊。
- 修改標準後，新檢驗使用新設定，舊檢驗保留快照。
- 必填檢驗項目未完成時，不得完成檢驗紀錄。

## 3. 建立檢驗批次

```text
QUALITY_MANAGER / INSPECTOR
  ↓
輸入批次代碼、產品與數量
  ↓
建立批次（PENDING）
  ↓
指派或選擇檢驗人員
  ↓
開始檢驗（INSPECTING）
```

規則：

- 批次代碼不可重複。
- 產品必須為 ACTIVE。
- 數量必須大於 0。
- CANCELLED 批次不可建立新的檢驗結果。

## 4. 執行檢驗

```text
檢驗人員開啟批次
  ↓
系統載入產品檢驗標準
  ↓
逐項輸入測量值或選擇結果
  ↓
系統判定單項 PASS / FAIL / NA
  ↓
保存當次標準快照
  ↓
完成所有必填項目
  ↓
計算整體結果
```

判定原則：

- 任一必要項目 FAIL，整體結果為 FAIL。
- 所有必要項目 PASS，整體結果為 PASS。
- 尚有必要項目未完成，整體結果為 PENDING。
- `NA` 只有在該項目允許不適用時才可使用。
- 數值項目可依標準上下限自動判定；文字、布林與選項依設定判定。

## 5. 不良品處理

```text
檢驗結果 FAIL
  ↓
建立不良品紀錄（NEW）
  ↓
選擇不良類型、填寫描述
  ↓
上傳一張或多張圖片
  ↓
品質主管確認（CONFIRMED）
  ↓
建立改善措施並指派負責人（PROCESSING）
```

規則：

- 不良品必須關聯檢驗紀錄與不良類型。
- 圖片檔案應限制格式、大小並進行安全檢查。
- 只有授權角色可以確認、解決或結案不良品。
- CLOSED 後不可直接修改核心內容，必要時建立更正紀錄。

## 6. 改善措施流程

```text
建立改善措施（PENDING）
  ↓
指派負責人與到期日
  ↓
開始處理（PROCESSING）
  ↓
填寫完成內容與完成時間
  ↓
品質主管確認（COMPLETED）
```

規則：

- `due_date` 不應早於建立日期，除非具備主管權限。
- 已逾期且未完成的措施應在看板標示。
- 一筆不良品的改善措施全部完成後，才可進入 RESOLVED。
- 結案操作需留下稽核紀錄。

## 7. API 與權限流程

```text
Client（Web / Android）
  ↓ JWT
Django REST API
  ↓ Authentication
Role Permission
  ↓ Validation
Service / Serializer
  ↓ Transaction
Django ORM
  ↓
MySQL
```

所有 API 應：

- 驗證登入狀態與角色權限。
- 驗證外鍵、狀態轉移與必要欄位。
- 對建立檢驗結果、不良品與改善措施使用交易。
- 回傳一致的錯誤格式。
- 不在回應中暴露密碼或敏感資料。

## 8. 建議 API 資源

```text
POST   /api/auth/login/
GET    /api/products/
POST   /api/products/
GET    /api/inspection-items/
POST   /api/products/{id}/inspection-items/
GET    /api/inspection-batches/
POST   /api/inspection-batches/
POST   /api/inspections/
POST   /api/inspections/{id}/results/
POST   /api/defects/
POST   /api/defects/{id}/images/
POST   /api/defects/{id}/corrective-actions/
PATCH  /api/corrective-actions/{id}/
GET    /api/reports/quality-summary/
```

## 9. 開發與驗收順序

1. 建立 Django 專案、MySQL 連線與環境設定。
2. 建立帳號、角色與權限測試。
3. 建立產品與檢驗標準 CRUD。
4. 建立批次與檢驗結果 API。
5. 驗證自動判定與標準快照。
6. 建立不良品、圖片與改善措施流程。
7. 建立稽核紀錄與報表。
8. 完成 Web 管理介面。
9. API 穩定後開發 Android Kotlin App。

最低可交付流程：

```text
登入 → 建立產品 → 設定檢驗標準 → 建立批次
→ 完成檢驗 → 產生不良品 → 指派改善措施 → 查詢結案狀態
```
