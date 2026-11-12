# 上課簽到機 - Google 試算表 (Google Sheets) 建立與雲端 API 部署指南

本指南詳細說明如何從零建立一份專屬的 Google 試算表，並透過 **Google Apps Script (GAS)** 部署為免驗證的輕量 REST API，供 ESP32-S3 / Pico 掌機在學生打卡時即時寫入簽到記錄。

---

## 步驟一：建立全新的 Google 試算表

1. 開啟瀏覽器，登入您的 Google 帳號。
2. 前往 [Google 試算表 (Google Sheets)](https://sheets.new)，建立一份空白試算表。
3. 將試算表標題命名為：`極客掌機_上課簽到簿`。
4. 將左下角的工作表名稱重新命名為：`簽到記錄`（**注意：名稱必須完全一致**）。
5. （選做）在第 1 列建立表頭欄位：
   - **A1**：`簽到時間`
   - **B1**：`姓名`
   - **C1**：`狀態`
   - *(若不手動建，GAS 程式在首次執行時也會自動為您建立)*。

---

## 步驟二：開啟並貼上 Google Apps Script 程式碼

1. 在試算表上方選單點選：**「擴充功能」 $\rightarrow$ 「Apps Script」**。
2. 進入 Apps Script 編輯器後，將左側預設的 `程式碼.gs` 內容全部清空。
3. 貼上專案中的 [`google_apps_script.js`](file:///d:/練習操作區/創客/上課簽到機/google_apps_script.js) 程式碼：

```javascript
// google_apps_script.js - 上課簽到機 Google Apps Script 雲端中繼服務
// 部署方式：部屬為 Web 應用程式 (Execute as: Me, Who has access: Anyone)

function doGet(e) {
  var name = (e && e.parameter && e.parameter.name) ? e.parameter.name : "未知學生";
  var timeStr = Utilities.formatDate(new Date(), "Asia/Taipei", "yyyy-MM-dd HH:mm:ss");

  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName("簽到記錄");
    if (!sheet) {
      sheet = ss.insertSheet("簽到記錄");
      sheet.appendRow(["簽到時間", "姓名", "狀態"]);
      sheet.getRange("A1:C1").setBackground("#4a86e8").setFontColor("#ffffff").setFontWeight("bold");
    }

    // 檢查今天是否已簽到過 (防重複機制)
    var data = sheet.getDataRange().getValues();
    var todayStr = Utilities.formatDate(new Date(), "Asia/Taipei", "yyyy-MM-dd");
    var isDuplicate = false;

    for (var i = 1; i < data.length; i++) {
      var rowTime = data[i][0];
      var rowName = data[i][1];
      if (rowTime && rowTime.toString().indexOf(todayStr) !== -1 && rowName === name) {
        isDuplicate = true;
        break;
      }
    }

    if (!isDuplicate) {
      sheet.appendRow([timeStr, name, "出席"]);
    }

    var result = {
      status: "success",
      name: name,
      time: timeStr,
      is_duplicate: isDuplicate,
      message: isDuplicate ? "Already checked in today" : "Check-in successful"
    };

    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    var errResult = {
      status: "error",
      error: err.toString()
    };
    return ContentService.createTextOutput(JSON.stringify(errResult))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
```

4. 點擊上方的 **「儲存」圖示（磁碟片）** 或按 `Ctrl + S`。

---

## 步驟三：部署為 Web 應用程式 (關鍵設定)

> [!IMPORTANT]
> 部署權限設定非常關鍵，若設定錯誤，掌機發送 HTTP 請求時會被 Google 登入頁面擋下（回傳 401/403）。

1. 點擊右上角藍色按鈕：**「部署」 $\rightarrow$ 「新增部署作業」**。
2. 點選左側齒輪圖示，選擇種類為：**「網路應用程式 (Web App)」**。
3. 填寫部署參數：
   - **說明**：`v2.0 繁體中文簽到 API`
   - **執行身分 (Execute as)**：選擇 **「我 (您的 Google 帳號)」**。
   - **誰可以存取 (Who has access)**：務必選擇 **「所有人 (Anyone)」**。
4. 點選右下角 **「部署」**。
5. （首次部署需授權）：
   - 點擊 **「審查權限」**。
   - 選擇您的 Google 帳號。
   - 若出現「Google 尚未驗證此應用程式」警告，點擊左下角 **「進階 (Advanced)」 $\rightarrow$ 「前往「極客掌機_上課簽到簿」(不安全)」**。
   - 點擊 **「允許 (Allow)」**。

---

## 步驟四：取得並填入 GAS_CHECKIN_SCRIPT_ID

1. 部署成功後，畫面會顯示 **「網路應用程式網址 (Web App URL)」**，格式如下：
   ```text
   https://script.google.com/macros/s/AKfycbxKgoNQivz1UFoJOTgo.../exec
   ```
2. 複製網址中 `/s/` 與 `/exec` 之間的那一長串代碼（即 `SCRIPT_ID`）。
3. 打開專案中的 [`config.py`](file:///d:/練習操作區/創客/上課簽到機/config.py)，將代碼貼入：
   ```python
   # 替換為您的新 ID
   GAS_CHECKIN_SCRIPT_ID = "您的_SCRIPT_ID"
   ```

---

## 步驟五：瀏覽器快速除錯與測試

在把程式燒入掌機前，您可以直接在電腦瀏覽器測試 API 是否正常：

1. 在瀏覽器網址列貼上以下網址（將 `SCRIPT_ID` 替換成您的）：
   ```text
   https://script.google.com/macros/s/您的_SCRIPT_ID/exec?name=陳大明
   ```
2. 按下 Enter，瀏覽器若回傳以下 JSON，代表部署 100% 成功：
   ```json
   {
     "status": "success",
     "name": "陳大明",
     "time": "2026-11-12 13:35:00",
     "is_duplicate": false,
     "message": "Check-in successful"
   }
   ```
3. 切回您的 Google 試算表，您會看見「簽到記錄」工作表已經自動多了一列：
   | 簽到時間 | 姓名 | 狀態 |
   | :--- | :--- | :--- |
   | 2026-11-12 13:35:00 | 陳大明 | 出席 |

4. 再次在瀏覽器按 F5 重整，會回傳 `"is_duplicate": true`，試算表不會重複增加列，證明防重複簽到機制運作正常！

---

## 步驟六：更新 MCU 配置

完成上述測試後，執行以下指令將新 ID 同步燒入掌機：

```powershell
cd "d:\練習操作區\創客\上課簽到機"
python -m mpremote connect COM4 cp config.py : + reset
```
