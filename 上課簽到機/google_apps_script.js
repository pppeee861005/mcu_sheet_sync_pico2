// google_apps_script.js - 上課簽到機 Google Apps Script 雲端中繼服務 (支援多班級自動分流)
// 部署方式：部屬為 Web 應用程式 (Execute as: Me, Who has access: Anyone)

function doGet(e) {
  var className = (e && e.parameter && e.parameter.class) ? e.parameter.class : "未指定班級";
  var name = (e && e.parameter && e.parameter.name) ? e.parameter.name : "未知學生";
  var timeStr = Utilities.formatDate(new Date(), "Asia/Taipei", "yyyy-MM-dd HH:mm:ss");
  var todayStr = Utilities.formatDate(new Date(), "Asia/Taipei", "yyyy-MM-dd");

  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    // 依班級名稱自動建立或選取專屬工作表
    var sheetName = className + "_簽到記錄";
    var sheet = ss.getSheetByName(sheetName);
    
    if (!sheet) {
      sheet = ss.insertSheet(sheetName);
      sheet.appendRow(["簽到時間", "班級", "姓名", "狀態"]);
      sheet.getRange("A1:D1").setBackground("#4a86e8").setFontColor("#ffffff").setFontWeight("bold");
    }

    // 檢查該班級今天是否已簽到過 (防重複機制)
    var data = sheet.getDataRange().getValues();
    var isDuplicate = false;

    for (var i = 1; i < data.length; i++) {
      var rowTime = data[i][0];
      var rowName = data[i][2];
      if (rowTime && rowTime.toString().indexOf(todayStr) !== -1 && rowName === name) {
        isDuplicate = true;
        break;
      }
    }

    if (!isDuplicate) {
      sheet.appendRow([timeStr, className, name, "出席"]);
    }

    var result = {
      status: "success",
      class: className,
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
