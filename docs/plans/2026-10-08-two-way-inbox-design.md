# TGGO 雙向收件匣設計

## 目標

讓固定 Telegram 管理者對話能把明確標記為 `/tggo` 的文字與附件安全保存到 TGGO 收件匣，供使用者之後透過 CLI 或 Codex 查看。Telegram 回傳內容只作為資料保存，不會執行 Codex、Shell、伺服器或其他外部操作。

## 使用體驗

- 純文字：在 Telegram 輸入 `/tggo 要保存的內容`。
- 附件：上傳圖片、影片、音訊或文件，並在附件說明輸入 `/tggo 附件的說明文字`。
- Bot 成功保存後回覆 `✅ 已存入 TGGO 收件匣｜編號 <ID>`。
- 沒有 `/tggo` 前綴的訊息不保存、不回覆。
- 非設定 Chat ID 的更新一律忽略。
- CLI 提供 `tggo inbox`、`tggo inbox show <ID>`、`tggo inbox download <ID>`、`tggo inbox read <ID>` 與 `tggo inbox archive <ID>`。

## 架構

採 Telegram Bot API 長輪詢，不新增公開 HTTP 端點。新增一個常駐 `tggo inbox-listen` 程序取得 updates，先以固定 Chat ID 和 `/tggo` 前綴過濾，再將文字、metadata 與附件寫入本機收件匣。

Direct 模式由本機接收；SSH Relay 模式由遠端 Relay 接收並保存於 Relay 收件匣，本機透過既有 SSH 信任邊界列出及下載項目。兩種模式共用相同的 inbox record 格式與 CLI 行為。

## 資料模型與儲存

預設資料目錄為 `~/.local/share/tggo/inbox/`：

- `index.json`：項目索引與狀態。
- `<item-id>/record.json`：不可變的訊息 metadata。
- `<item-id>/files/`：Telegram 附件原始檔。

每筆項目包含 TGGO ID、Telegram update/message/file ID、chat ID、收到時間、文字、附件說明、附件檔名、MIME、大小、SHA-256、讀取狀態與封存狀態。索引採原子替換寫入，Telegram update ID 作為去重鍵，避免重啟後重複保存。

## 安全邊界

- 只接受設定檔中的 `TGGO_CHAT_ID`。
- `/tggo` 必須位於文字或 caption 開頭；不解析其後內容為命令。
- 不執行、不解壓、不預覽附件內容。
- 下載前檢查 Telegram 回報大小，套用既有單檔及總容量限制。
- 檔名經 basename 與安全字元正規化，阻擋絕對路徑、`..` 與符號連結。
- Token 不寫入收件匣、索引、日誌或 Git。
- 本機資料目錄為 `0700`，檔案為 `0600`。
- Bot 的確認回覆不包含本機路徑或機密資訊。

## 長輪詢與錯誤處理

接收器使用 `getUpdates` 並持久化 offset。只有在項目及附件完整落盤後才推進 offset；不確定結果會保留 update 供下次重試。Telegram 暫時失敗採有上限的指數退避。單筆格式或附件錯誤會回覆保存失敗，但不能阻塞後續 updates。

若相同 update 再次出現，接收器回傳既有 TGGO ID，不建立重複項目。Bot 確認訊息失敗不撤銷已完成的本機保存。

## 安裝與運行

安裝器加入接收器，但不會自動啟動未設定的服務。文件提供 macOS LaunchAgent 與 Linux systemd user service 的安裝方式；亦可前景執行 `tggo inbox-listen` 供除錯。

既有單向傳送介面保持相容。新增的接收功能使用同一組 Bot Token 與 Chat ID，不增加第二組憑證。

## 驗收標準

- 指定 chat 的 `/tggo 文字` 能保存並收到編號回覆。
- 附件 caption 使用 `/tggo 說明` 時，文字與附件完整保存且 SHA-256 正確。
- 一般訊息與其他 chat 不產生收件匣項目。
- 重複 update 不重複保存。
- CLI 能列出、查看、下載、標記已讀與封存。
- Direct 與 SSH Relay 的行為一致。
- 路徑穿越、超限附件和未授權 chat 測試通過。
- 現有 send、preview、doctor、安裝與解除安裝測試不得退化。

