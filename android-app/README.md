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
- `POST /api/inspection/submit/`

目前 Android 端預設依據現有後端 contract 提交：

```json
{
  "batch_id": 1,
  "remark": "首件檢驗",
  "results": [
    {
      "item_id": 1,
      "measured_value": 5.10,
      "result": "PASS",
      "remark": "穩定"
    }
  ]
}
```

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
