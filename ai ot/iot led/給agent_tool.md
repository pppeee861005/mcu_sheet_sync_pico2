你需要把它包裝成一個「工具函式」，而不是只提供一段 URL。最簡單的工具定義如下：

  {
    "name": "turn_on_led",
    "description": "開啟 AIoT LED 燈",
    "parameters": {
      "type": "object",
      "properties": {},
      "required": []
    }
  }

  當 Agent 呼叫 turn_on_led 時，工具執行：

  import requests

  def turn_on_led():
      response = requests.get(
          "https://pico-vercel-server-ha114j163-pperters-projects.vercel.app/api/on",
          timeout=10
      )
      return response.json()

  Agent 的流程會是：

  使用者：幫我開燈
  Agent：呼叫 turn_on_led
  Tool：GET /api/on
  Vercel：寫入 LED_ON
  Pico：讀取 LED_ON 並開燈

  如果你的 Agent 平台只支援 HTTP Tool，則設定：

  Method: GET
  URL: https://pico-vercel-server-ha114j163-pperters-projects.vercel.app/api/on
  Name: turn_on_led

  關燈則建立另一個工具：

  GET https://pico-vercel-server-ha114j163-pperters-projects.vercel.app/api/off

  注意：目前這個 URL 沒有驗證，任何取得網址的人都能控制 LED；正式使用建議加上 API 金鑰。