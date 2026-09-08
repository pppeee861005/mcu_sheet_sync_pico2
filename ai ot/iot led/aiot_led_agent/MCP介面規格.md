# MCP 介面規格

## 目的

將既有 LED HTTP API 包裝成 LangChain 可使用的 MCP 工具。

## 建議工具

```text
control_led(action)
```

## action 白名單

| action | HTTP 端點 | 說明 |
|---|---|---|
| `on` | `GET /api/on` | 開燈 |
| `off` | `GET /api/off` | 關燈 |
| `status` | `GET /api/command` | 查詢狀態 |

Agent 不得自行產生其他 URL 或 action。

## 回應

工具應回傳 HTTP 狀態碼與 API JSON。只有 API 成功回應時，才可回報操作成功。

## 待確認項目

- MCP Server 的實際啟動命令
- MCP 傳輸方式：stdio、SSE 或 Streamable HTTP
- 實際工具名稱是否為 `control_led`
