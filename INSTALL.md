# 安装并执行姜胡说知识库 Skill

用户把本地址交给 Agent，就是请求安装并执行本 skill。完整获取、宿主安装、Obsidian 安装、建库、首次登记、报错恢复与验收要求都定义在根目录 `SKILL.md`，不需要用户另外粘贴执行清单。

- 仓库：https://github.com/hanyh56/jianghushuo-kb-setup
- 完整 ZIP：https://github.com/hanyh56/jianghushuo-kb-setup/archive/refs/heads/main.zip

Agent 先用 Git 或本机下载工具获取并解压完整包，保留 `SKILL.md`、`assets/`、`scripts/`、`references/`，再读取 `SKILL.md` 继续执行，默认统一入口为 `scripts/setup.py`。不要只下载这份说明或一张 SKILL.md；已有同名目录先比较，保留原有内容。

本 skill 由维护者发布在 GitHub，尚未上架 SkillHub / ClawHub。市场搜索无结果时继续使用指定来源；不要因市场查不到而停止，也不要安装名称近似的其他 skill。

## WorkBuddy

按 [官方说明](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)，普通对话安装仅支持市场技能；自定义包通过「专家·技能·连接器」→「技能」→「添加技能」→「上传技能」导入。在「已安装」中确认启用后，输入“使用 jianghushuo-kb-setup”即可触发内部完整流程。

具备桌面工具的 Agent 代操作导入；只能本人操作时，先备好完整 ZIP，只交接上传这一步。若版本不接受 GitHub ZIP 外层目录，解压后把包含 `SKILL.md` 与全部配套文件的技能目录重新打包上传。能从链接读取并执行文件，不等于宿主已持久安装，需分别核实。

## 更新已有安装或修复打开失败

Agent 获取新版完整包并读取新版 `SKILL.md`。从新版目录使用 `scripts/setup.py` 的 `--update-skill` 备份更新安装 skill，复用实际原知识库与宿主目录，不重建、不迁移个人笔记。

Windows 等系统出现 “Vault not found” 时，按照 skill 内的恢复流程，打开 Vault 管理器并选择现有文件夹，再使用登记后的 Vault ID 打开工作台。不能将 `open?path=…` 当作注册库的方法。
