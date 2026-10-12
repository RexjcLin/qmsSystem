# QMS Android MVP

此資料夾提供 Android Studio 可直接開啟的 QMS 行動端骨架，對應目前 Django 專案已存在的檢驗 API。

## 已實作的核心畫面

- 登入頁（Basic Auth 驗證 + 本機保存授權 header）
- 待檢驗批次列表頁
- 產品檢驗項目頁
- 檢驗結果填寫／送出頁

## 對應後端 API

- `GET /api/inspection/pending/`
- `GET /api/products/{product_id}/inspection-items/`
- `POST /api/inspection/batches/{batch_id}/start/`
- `POST /api/inspection/batches/{batch_id}/release/`
- `POST /api/inspection/submit/`

目前 Android 端預設依據現有後端 contract 提交：

```json
{
  "batch_id": 1,
  "remark": "首件檢驗",
  "results": [
    {
      "product_item_id": 1,
      "measured_value": 5.10,
      "result": "PASS",
      "remark": "穩定"
    }
  ]
}
```

`product_item_id` 使用檢驗項目 API 回傳的產品項目關聯 ID，不是通用的 `item_id`。App 內部表單與草稿的 `itemId` 也使用此關聯 ID。

進入填寫頁會開始或續作該批次；只有負責人可以提交。返回不會自動釋放批次，可重新進入續作，或使用填寫頁的停止按鈕釋放。草稿目前只保留在 ViewModel 記憶體中，沒有離線或跨 App 重啟保存。主管可透過釋放 API 解除他人占用。

有數值上下限的項目，選 PASS 或 FAIL 都必須填量測值；超規不能選 PASS。必填項目不能選 NA，且檢驗不能空白或全為 NA。後端回傳的驗證錯誤會顯示在畫面上。

送出成功後會顯示結果及缺陷數量，並停用重複送出；每個 FAIL 項目會自動建立 NEW 缺陷。缺陷分類調整、照片與改善措施由 Django 後台接續處理。

## 在 Android Studio 開啟

1. 開啟 Android Studio
2. 選擇 `Open`
3. 指到 `/home/runner/work/qmsSystem/qmsSystem/android-app`
4. 等待 Gradle Sync 完成

## Base URL

預設 API Base URL：

- Emulator：`http://10.0.2.2:8000/api/`

若你使用真機或不同開發環境，請修改：

- `app/build.gradle.kts` 內的 `BuildConfig.API_BASE_URL`

## 驗證

```bash
./gradlew test
./gradlew assembleDebug
```
