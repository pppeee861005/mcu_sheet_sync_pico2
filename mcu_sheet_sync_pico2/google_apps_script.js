/**
 * Google Apps Script (GAS) 接收端程式碼
 * 同時支援 POST (JSON) 與 GET (Query Parameters) 讀寫 Google 試算表！
 * 
 * 系統支援：
 * 1. Sheet Sync (上報計數/事件日誌)
 * 2. CloudMsg (讀取/發布看板訊息)
 * 3. AI 智慧農業 (讀取 FarmData 最新環境數據、寫入 FarmLogs 推理日誌)
 */

function getOrCreateSheet(ss, sheetName, headers) {
  var sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
  }
  if (sheet.getLastRow() === 0 && headers && headers.length > 0) {
    sheet.appendRow(headers);
  }
  return sheet;
}

function handleData(params) {
  var lock = LockService.getScriptLock();
  lock.tryLock(10000);

  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var timestamp = Utilities.formatDate(new Date(), "Asia/Taipei", "yyyy-MM-dd HH:mm:ss");
    var action = params.action || "";

    // ── 子系統 3：AI 農業決策日誌儲存 ──
    if (action === "log_ai_decision" || params.event === "AI_Agri_Decision") {
      var logSheet = getOrCreateSheet(ss, "FarmLogs", [
        "時間戳記", "裝置名稱", "決策動作", "決策原由", "空氣濕度", "氣溫", "土壤乾度", "土壤EC", "降雨預報"
      ]);

      var device = params.device || "Pico2W";
      var decision = params.decision || "UNKNOWN";
      var reason = params.reason || "";
      var humidity = params.humidity !== undefined ? params.humidity : "";
      var temp = params.temp !== undefined ? params.temp : "";
      var soilDry = params.soil_dryness !== undefined ? params.soil_dryness : "";
      var soilEc = params.soil_ec !== undefined ? params.soil_ec : "";
      var rainForecast = params.rain_forecast !== undefined ? params.rain_forecast : "";

      logSheet.appendRow([timestamp, device, decision, reason, humidity, temp, soilDry, soilEc, rainForecast]);

      return ContentService.createTextOutput(JSON.stringify({
        "status": "success",
        "type": "ai_log",
        "timestamp": timestamp,
        "decision": decision,
        "reason": reason
      })).setMimeType(ContentService.MimeType.JSON);
    }

    // ── 一般事件與計數上報 ──
    var defaultSheet = ss.getActiveSheet();
    if (defaultSheet.getLastRow() === 0) {
      defaultSheet.appendRow(["時間戳記", "裝置名稱", "事件類型", "觸發次數", "備註"]);
    }

    var device = params.device || "Pico2W";
    var event = params.event || "Button_Press";
    var pressCount = (params.count !== undefined) ? params.count : ((params.press_count !== undefined) ? params.press_count : "");
    var message = params.msg || params.message || (params.reason ? params.reason : "狀態同步");

    defaultSheet.appendRow([timestamp, device, event, pressCount, message]);

    return ContentService.createTextOutput(JSON.stringify({
      "status": "success",
      "timestamp": timestamp,
      "press_count": pressCount,
      "event": event,
      "message": message
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

// 支援 GET
function doGet(e) {
  var params = (e && e.parameter) ? e.parameter : {};
  var ss = SpreadsheetApp.getActiveSpreadsheet();

  // 動作 1：讀取最新留言 (雲端看板功能)
  if (params.action === "get_msg") {
    try {
      var sheet = ss.getActiveSheet();
      var lastRow = sheet.getLastRow();
      var msg = "No Message";
      var sender = "Cloud";
      var timeStr = "";
      
      if (lastRow > 1) {
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

  // 動作 2：讀取農田環境數據 (系統三：AI 農業專用，只從當前作用工作表或指定表的 E 欄抓取最新一列)
  if (params.action === "get_farm_data") {
    try {
      var sheet = ss.getSheetByName("FarmData") || ss.getActiveSheet();
      
      // 若是全新空白表，自動於 E1 與 E2 建立項目欄位說明與示範虛擬數據
      if (sheet.getLastRow() === 0 || !sheet.getRange("E1").getValue()) {
        sheet.getRange("E1").setValue("空氣濕度(%),氣溫(C),土壤乾度(%),土壤EC,降雨預報");
        sheet.getRange("E2").setValue("65,28.5,82,1.2,No Rain");
      }

      var lastRow = sheet.getLastRow();
      if (lastRow <= 1) {
        return ContentService.createTextOutput(JSON.stringify({
          "status": "no_data",
          "message": "No data in column E"
        })).setMimeType(ContentService.MimeType.JSON);
      }

      // 從第 E 欄由下往上找出最新一筆有資料的儲存格
      var rawString = "";
      for (var r = lastRow; r >= 2; r--) {
        var val = sheet.getRange(r, 5).getValue(); // 第 5 欄即為 E 欄
        if (val !== undefined && val !== null && String(val).trim() !== "") {
          rawString = String(val).trim();
          break;
        }
      }

      if (!rawString) {
        return ContentService.createTextOutput(JSON.stringify({
          "status": "no_data",
          "message": "No valid data found in column E"
        })).setMimeType(ContentService.MimeType.JSON);
      }

      // 支援以半形逗號或全形逗號切分：空氣濕度,氣溫,土壤乾度,土壤電解質,降雨預報
      var parts = rawString.replace(/，/g, ",").split(",").map(function(s) { return s.trim(); });

      if (parts.length < 5) {
        return ContentService.createTextOutput(JSON.stringify({
          "status": "no_data",
          "message": "Incomplete items in column E"
        })).setMimeType(ContentService.MimeType.JSON);
      }

      var humidity = Number(parts[0]);
      var temp = Number(parts[1]);
      var soilDry = Number(parts[2]);
      var soilEc = Number(parts[3]);
      var rainForecast = parts[4];

      if (isNaN(humidity) || isNaN(temp) || isNaN(soilDry)) {
        return ContentService.createTextOutput(JSON.stringify({
          "status": "no_data",
          "message": "Invalid numeric format in column E"
        })).setMimeType(ContentService.MimeType.JSON);
      }

      return ContentService.createTextOutput(JSON.stringify({
        "status": "success",
        "raw": rawString,
        "humidity": humidity,
        "temp": temp,
        "soil_dryness": soilDry,
        "soil_ec": isNaN(soilEc) ? 1.0 : soilEc,
        "rain_forecast": rainForecast
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
