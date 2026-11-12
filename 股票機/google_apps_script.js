/**
 * 股票機專用 - Google Apps Script (GAS) 試算表綁定版
 * 
 * 參考來源：stocks.py (TWSE FMTQIK 大盤指數 API)
 * 功能：
 *  1. 向台灣證交所爬取最新大盤指數與今日漲跌點數。
 *  2. 自動將每日/即時行情記錄進 Google 試算表「大盤歷史」工作表（歷史存檔與儀表板）。
 *  3. 回傳 MicroPython (Pico 2 W) 最易解析的極簡 JSON 格式 (< 150 bytes)。
 */

function doGet(e) {
  try {
    const stockData = fetchAndRecordTwseTaiex();
    return ContentService.createTextOutput(JSON.stringify(stockData))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    const errorResponse = {
      status: "error",
      message: error.toString(),
      timestamp: new Date().toISOString()
    };
    return ContentService.createTextOutput(JSON.stringify(errorResponse))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * 抓取大盤並記錄至試算表
 */
function fetchAndRecordTwseTaiex() {
  const stockData = fetchTwseTaiex();

  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    if (ss) {
      let sheet = ss.getSheetByName("大盤歷史");
      if (!sheet) {
        sheet = ss.insertSheet("大盤歷史");
        sheet.appendRow(["更新時間", "交易日期", "大盤指數", "漲跌點數", "趨勢方向", "查詢來源"]);
      }

      const lastRow = sheet.getLastRow();
      let shouldAppend = true;

      // 檢查最後一列：若已存在相同交易日，則原地更新；若為新交易日則新增一列
      if (lastRow > 1) {
        const lastDate = sheet.getRange(lastRow, 2).getValue().toString();
        if (lastDate === stockData.date) {
          sheet.getRange(lastRow, 1).setValue(stockData.timestamp);
          sheet.getRange(lastRow, 3).setValue(stockData.index);
          sheet.getRange(lastRow, 4).setValue(stockData.change);
          sheet.getRange(lastRow, 5).setValue(stockData.direction);
          shouldAppend = false;
        }
      }

      if (shouldAppend) {
        sheet.appendRow([
          stockData.timestamp,
          stockData.date,
          stockData.index,
          stockData.change,
          stockData.direction,
          "Pico_2_W"
        ]);
      }
    }
  } catch (err) {
    Logger.log("記錄進試算表時發生錯誤: " + err);
  }

  return stockData;
}

/**
 * 爬取證交所 FMTQIK 大盤指數核心
 */
function fetchTwseTaiex() {
  const now = new Date();
  let year = now.getFullYear();
  let month = now.getMonth() + 1;

  const urlTemplate = "https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK?date={date}&response=json";
  const headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
  };

  // 最多向前回溯查詢 3 個月，確保假日或長假也能抓到最新交易日
  for (let i = 0; i < 3; i++) {
    const monthStr = month < 10 ? "0" + month : "" + month;
    const dateStr = `${year}${monthStr}01`;
    const targetUrl = urlTemplate.replace("{date}", dateStr);

    try {
      const response = UrlFetchApp.fetch(targetUrl, {
        headers: headers,
        muteHttpExceptions: true
      });

      if (response.getResponseCode() === 200) {
        const json = JSON.parse(response.getContentText());
        if (json.stat === "OK" && json.data && json.data.length > 0) {
          const latestRow = json.data[json.data.length - 1];
          const tradeDate = latestRow[0];        // 例如 "113/11/11"
          const indexStr = latestRow[4];         // 例如 "23,522.53"
          let changeStr = latestRow[5];          // 例如 "+148.87" 或 "-32.10"

          let direction = "FLAT";
          if (changeStr.includes("+") || (!changeStr.includes("-") && parseFloat(changeStr.replace(/,/g, "")) > 0)) {
            direction = "UP";
            if (!changeStr.startsWith("+")) changeStr = "+" + changeStr;
          } else if (changeStr.includes("-") || parseFloat(changeStr.replace(/,/g, "")) < 0) {
            direction = "DOWN";
          }

          return {
            status: "success",
            date: tradeDate,
            index: indexStr,
            change: changeStr,
            direction: direction,
            timestamp: Utilities.formatDate(new Date(), "Asia/Taipei", "yyyy-MM-dd HH:mm:ss")
          };
        }
      }
    } catch (e) {
      Logger.log("Fetch error on " + dateStr + ": " + e);
    }

    if (month === 1) {
      year -= 1;
      month = 12;
    } else {
      month -= 1;
    }
  }

  throw new Error("無法從證交所獲取大盤行情資料");
}
