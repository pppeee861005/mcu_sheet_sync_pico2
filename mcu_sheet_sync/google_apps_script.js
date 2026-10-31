/**
 * Google Apps Script (GAS) 接收端程式碼
 * 同時支援 POST (JSON) 與 GET (Query Parameters) 寫入 Google 試算表！
 * 
 * 為什麼要支援 GET？
 * 因為 MicroPython 內建的 urequests 在處理 Google 伺服器的 302 重定向與 TLS POST 時，
 * Google 伺服器常會判定格式不合拋出 400 Bad Request；
 * 改用 GET Query URL 傳遞，MicroPython 與 Google 之間 100% 穩定且無需額外依賴庫！
 */

function handleData(params) {
  var lock = LockService.getScriptLock();
  lock.tryLock(10000);

  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    
    // 如果是全新表單且第 1 行是空的，自動建立標題列
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(["時間戳記", "裝置名稱", "事件類型", "觸發次數", "備註"]);
    }

    // 格式化目前伺服器時間 (台北時區 GMT+8)
    var timestamp = Utilities.formatDate(new Date(), "Asia/Taipei", "yyyy-MM-dd HH:mm:ss");

    var device = params.device || "ESP32-S3";
    var event = params.event || "Button_Press";
    var pressCount = (params.press_count !== undefined) ? params.press_count : "";
    var message = params.message || "按鍵觸發狀態同步";

    // 追加寫入試算表新列
    sheet.appendRow([timestamp, device, event, pressCount, message]);

    return ContentService.createTextOutput(JSON.stringify({
      "status": "success",
      "timestamp": timestamp,
      "press_count": pressCount,
      "event": event
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      "status": "error",
      "message": error.toString()
    })).setMimeType(ContentService.MimeType.JSON);

  } finally {
    lock.releaseLock();
  }
}

// 支援 POST
function doPost(e) {
  var data = {};
  if (e && e.postData && e.postData.contents) {
    try {
      data = JSON.parse(e.postData.contents);
    } catch (err) {
      data = { "message": e.postData.contents };
    }
  }
  return handleData(data);
}

// 支援 GET (MCU 傳遞 ?action=read_latest 或 ?device=SkySync_ESP32&event=Weather_RAIN...)
function doGet(e) {
  var params = (e && e.parameter) ? e.parameter : {};
  
  // 動作 1：讀取最新留言 (雲端悄悄話功能)
  if (params.action === "get_msg") {
    try {
      var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
      var lastRow = sheet.getLastRow();
      var msg = "No Message";
      var sender = "Cloud";
      var timeStr = "";
      
      if (lastRow > 1) {
        // 取得最後一列的資料 (時間戳記, 裝置名稱, 事件, 次數, 備註/訊息)
        var rowData = sheet.getRange(lastRow, 1, 1, 5).getValues()[0];
        timeStr = rowData[0] ? String(rowData[0]).substring(11, 16) : "";
        sender = rowData[1] || "Cloud";
        msg = rowData[4] || rowData[2] || "Hello!";
      } else {
        msg = "Welcome to SkyDeck!";
      }
      
      return ContentService.createTextOutput(JSON.stringify({
        "status": "success",
        "time": timeStr,
        "sender": sender,
        "message": msg
      })).setMimeType(ContentService.MimeType.JSON);
    } catch (err) {
      return ContentService.createTextOutput(JSON.stringify({
        "status": "error",
        "message": err.toString()
      })).setMimeType(ContentService.MimeType.JSON);
    }
  }

  // 如果沒有帶任何參數，回傳健康檢查資訊
  if (Object.keys(params).length === 0) {
    return ContentService.createTextOutput(JSON.stringify({
      "status": "active",
      "message": "SkyDeck OS API 運作中"
    })).setMimeType(ContentService.MimeType.JSON);
  }
  
  return handleData(params);
}
