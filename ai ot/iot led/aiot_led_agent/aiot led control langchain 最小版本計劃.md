# AIoT LED Control LangChain 最小版本計劃

## 1. 目標

建立一個只負責控制 LED 的輕量 LangChain Agent，支援：

- 開燈
- 關燈
- 查詢狀態

沿用現有的 LED Skill、MCP 與 HTTP API，不重新實作硬體控制。

## 2. 系統架構

```text
手機／網頁／命令列
        ↓
LangChain Agent
        ↓
LED MCP Tools
        ↓
既有 HTTP API
        ↓
Pico 2 W + WS2812 LED
```

## 3. 最小功能範圍

### Agent

- 接收自然語言指令
- 判斷 `on`、`off`、`status`
- 只允許呼叫 LED 工具
- 回傳 API 的 JSON 結果

### MCP 工具

統一提供一個工具：

```json
{
  "name": "control_led",
  "action": "on | off | status"
}
```

工具內部對應既有端點：

```text
on     → GET /api/on
off    → GET /api/off
status → GET /api/command
```

## 4. 建議技術選擇

- Python 3.11+
- LangChain 1.x
- `langchain-openai`
- 現有 LED MCP Server
- `python-dotenv` 管理模型金鑰
- `requests` 或 MCP Client 連接既有服務

不加入記憶、瀏覽器、Shell、檔案系統或多 Agent 功能。

## 5. 實作階段

### Phase 1：確認既有介面

- 確認 MCP Server 可正常啟動
- 確認 `on`、`off`、`status` 三個操作
- 確認 HTTP API 錯誤時會回傳失敗狀態

### Phase 2：建立 LangChain Adapter

- 將 MCP tools 轉成 LangChain tools
- 建立 LED 專用 system prompt
- 限制 Agent 只能使用 LED 工具

### Phase 3：建立最小入口

先提供命令列介面：

```text
> 幫我開燈
LED_ON

> 現在是什麼狀態？
LED_ON
```

### Phase 4：驗證

- 測試「開燈」
- 測試「關燈」
- 測試「查詢狀態」
- 測試不支援指令時拒絕執行
- 測試 API 失敗時不宣稱 LED 已改變

## 6. 安全限制

- 只允許固定的 `on`、`off`、`status`
- 不接受模型自行產生 URL
- 不允許 Shell 或任意 HTTP 請求
- 不把 API 金鑰寫入程式碼
- HTTP timeout 建議設定為 10 秒
- 關燈與開燈結果必須以 API 回應為準

## 7. 完成標準

以下條件全部達成即算完成：

1. LangChain Agent 可理解三種自然語言指令。
2. MCP 工具能正確呼叫現有 API。
3. LED 實體狀態與回應一致。
4. 不支援的要求不會執行其他操作。
5. 可在本機以單一命令啟動。

## 8. 後續可選擇擴充

- FastAPI 或 Flask HTTP 入口
- Telegram／LINE／手機前端
- 語音輸入
- 多顆 LED 或顏色控制
- 操作日誌與權限驗證

這些功能不列入最小版本。
