# AIoT LED Control LangChain Agent

這是一個使用 Python LangChain 建立的最小化 AI Agent，專門控制 AIoT WS2812 LED。

## 支援功能

- 開燈
- 關燈
- 查詢狀態

## 架構

```text
使用者 → LangChain Agent → LED MCP Tool → HTTP API → Pico 2 W → WS2812
```

## 安裝

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

複製 `.env.example` 為 `.env`，填入模型金鑰後再啟動 Agent。

## 安全原則

Agent 只允許控制 LED，不提供 Shell、檔案系統、瀏覽器或任意 HTTP 工具。

## 版本管理方式

本專案同時使用版本目錄與 Git：

```text
aiot_led_langchain_agent/
├── v0.0_codex/
├── v0.1_python_agent/
└── v1.0_web_app/
```

- 版本目錄：依產品階段整理程式、計劃、測試與部署文件。
- Git：記錄每次修改、比較差異與回復歷史版本。
- Git tag：標記正式版本，例如 `v0.0.0`、`v0.1.0`、`v1.0.0`。
- Git branch：開發尚未完成的新功能或新版本。

因此三個目錄與 Git 並非二選一：目錄負責組織專案，Git 負責版本控制，tag 負責標記發布版本。

完成一個版本後，建議執行：

```powershell
git add .
git commit -m "完成 v0.1 本機 LED Agent"
git tag v0.1.0
```
