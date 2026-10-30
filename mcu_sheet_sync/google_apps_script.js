/**
 * Google Apps Script (GAS) 接收端程式碼
 * 用途：接收來自 ESP32 / MCU (MicroPython) 的 HTTP POST 請求，並將資料寫入當前試算表。
 * 
 * 使用方式：
 * 1. 打開 Google 試算表 -> 擴充功能 -> Apps Script
 * 2. 清空原本的代碼，將本檔案全部內容複製貼上
 * 3. 點選右上角「部署」->「新增部署作業」->「網頁應用程式 (Web app)」
 *    - 執行身分：我 (Me)
 *    - 誰可以存取：任何人 (Anyone)
 * 4. 複製生成的 Web 應用程式網址，填入 main.py 中的 GAS_URL
 */

function doPost(e) {
  var lock = LockService.getScriptLock();
  // 最多等待 10 秒取得鎖，防止多筆資料同時寫入衝突
  lock.tryLock(10000);

  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    
    // 如果是全新表單且第 1 行是空的，自動建立標題列
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(["時間戳記", "裝置名稱", "事件類型", "觸發次數", "備註"]);
    }

    // 解析 MCU 送過來的 JSON 數據
    var rawData = e.postData.contents;
    var data = JSON.parse(rawData);

    // 格式化目前伺服器時間 (台北時區 GMT+8)
    var timestamp = Utilities.formatDate(new Date(), "Asia/Taipei", "yyyy-MM-dd HH:mm:ss");

    // 提取數據
    var device = data.device || "ESP32-S3";
    var event = data.event || "Button_Press";
    var pressCount = (data.press_count !== undefined) ? data.press_count : "";
    var message = data.message || "手動按鍵觸發寫入";

    // 將資料追加寫入試算表新列
    sheet.appendRow([timestamp, device, event, pressCount, message]);

    // 回傳成功 JSON 回應給 MCU
    return ContentService.createTextOutput(JSON.stringify({
      "status": "success",
      "timestamp": timestamp,
      "press_count": pressCount
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    // 錯誤處理
    return ContentService.createTextOutput(JSON.stringify({
      "status": "error",
      "message": error.toString()
    })).setMimeType(ContentService.MimeType.JSON);

  } finally {
    // 釋放鎖定
    lock.releaseLock();
  }
}

// 支援瀏覽器直接點開網址時做自我檢查 (GET 測試)
function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    "status": "active",
    "message": "MCU Sheet Sync Web App API 運作中！請使用 HTTP POST 發送數據。"
  })).setMimeType(ContentService.MimeType.JSON);
}
