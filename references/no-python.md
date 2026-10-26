# 没有 Python 也继续完成

这不是一个必须安装 Python 的产品。Agent 有文件读写和桌面工具时，按以下方法落地；只缺终端时不要让用户先安装依赖。

1. 通过 Git、ZIP 或可读取仓库目录的连接器取得完整内容。文件清单在 `assets/vault-manifest.json`。保持所有中文相对路径，将 `assets/vault/` 的文件复制到实际 Vault，已有文件先比较，不覆盖用户修改。
2. 按本机官方安装流程检测、下载并安装 Obsidian。已有则复用。下载页为 https://obsidian.md/download 。没有自动安装器的执行能力但有桌面工具时，直接操作官方图形安装器。
3. 建立日记目录 `02-Areas-长期领域/每日记录/`。在库内 `.obsidian/` 合并以下设置；修改前保存旧文件原始字节，无关字段保留，格式无效时先修复或询问真实冲突，不盲目覆盖。

`app.json`：

```json
{"alwaysUpdateLinks":true,"newFileLocation":"folder","newFileFolderPath":"00-灵感与收件箱"}
```

`templates.json`：

```json
{"folder":"90-系统/模板","dateFormat":"YYYY-MM-DD","timeFormat":"HH:mm"}
```

`daily-notes.json`：

```json
{"folder":"02-Areas-长期领域/每日记录","format":"YYYY-MM-DD","template":"90-系统/模板/模板-每日进度"}
```

`core-plugins.json` 支持对象或字符串列表。保留现有插件，只启用/添加 `file-explorer`、`global-search`、`switcher`、`command-palette`、`backlink`、`properties`、`templates`、`daily-notes`、`bases`。缺失时创建只包含这些项的配置，不下载社区插件。

4. 读取 `assets/runtime-skill.md`，把 `{{VAULT_PATH_JSON}}` 替换为该用户真实绝对路径的 JSON 字符串（引号与反斜杠正确转义），存为实际宿主 skills 根目录的 `personal-kb/SKILL.md`。已有其他同名 skill 时保留并处理冲突。只有指令文件机制则追加同等路径与规则入口，原内容保留。
5. 在 Obsidian 选择“打开文件夹作为仓库”，选中准确 Vault，再打开“知识资产工作台”。确认动态列表与六类目录可见。
6. 在收件箱创建带随机唯一标记的临时测试笔记，明确写“这是安装测试，不是本人经历”；用 Agent 回读并按该标记检索，再清理**自己创建的测试文件**。不得删除原有笔记。实际读入口与运行 skill，验证路径可访问；对模板、链接和相关设置回读检查。

与脚本路径的验收标准一致：文件结构、基础配置、Agent 入口、Obsidian 安装、Vault 登记与工作台显示分别有证据。没有持久存储或本地桌面权限时，明确报告缺少的能力，不编造完成状态。
