// google_apps_script.js - 上課簽到機 Google Apps Script 雲端中繼服務
// 部署方式：部屬為 Web 應用程式 (Execute as: Me, Who has access: Anyone)

function doGet(e) {
  var name = (e && e.parameter && e.parameter.name) ? e.parameter.name : "Unknown";
  var timeStr = Utilities.formatDate(new Date(), "Asia/Taipei", "yyyy-MM-dd HH:mm:ss");

  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName("簽到記錄");
    if (!sheet) {
      sheet = ss.insertSheet("簽到記錄");
      sheet.appendRow(["簽到時間", "姓名", "狀態"]);
      sheet.getRange("A1:C1").setBackground("#4a86e8").setFontColor("#ffffff").setFontWeight("bold");
    }

    // 檢查今天是否已簽到過
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
