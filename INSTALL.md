# 让 Agent 一次完成知识库落地

本入口用于用户明确请求安装这套知识库。下载完整仓库，再读取根目录 `SKILL.md`；不要只保存本文件或 SKILL.md 而遗漏 assets、scripts 与 references。

本 skill 的发布来源是下面的 GitHub 仓库，尚未由维护者上架到 SkillHub 或 ClawHub。只按名称搜索技能市场，找不到不能判定本仓库不存在；收到此地址后，直接读取并获取本仓库。

- 仓库：https://github.com/hanyh56/jianghushuo-kb-setup
- ZIP：https://github.com/hanyh56/jianghushuo-kb-setup/archive/refs/heads/main.zip

## WorkBuddy 用户先导入技能包

WorkBuddy 官方说明，普通对话安装仅支持技能市场中的技能；自定义技能包使用上传导入。因此推荐：

1. 下载上面的完整 ZIP。
2. 打开 WorkBuddy 左侧「专家·技能·连接器」→「技能」→「添加技能」→「上传技能」，选择 ZIP。
3. 在「已安装」中确认 `jianghushuo-kb-setup` 已出现并启用。若当前版本不接受 GitHub ZIP 的外层目录，解压后将包含 `SKILL.md`、`assets/`、`scripts/` 和 `references/` 的完整技能目录重新打包再上传。
4. 输入：使用 jianghushuo-kb-setup，完整安装我的 Obsidian 个人知识库，搭好目录、模板和工作台，配置后续使用入口，并完成读写验收。已有内容保留。

若 WorkBuddy 能从链接读取文件并执行本机命令，也可直接获取本仓库、审阅后读取 `SKILL.md` 执行；这不等于技能已出现在「已安装」列表。持久安装与后续入口需要分别验证，不因市场无结果而反复搜索或安装名称相近的技能。

官方说明：https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market

## 获取完整文件后继续执行

有 Git 可克隆；没有 Git 则用本机下载工具取 ZIP，再用系统解压工具或 Python 标准库解压。已有同名目录先读现状，不覆盖或删除。临时下载可以放缓存，实际知识库必须放持久目录。

下载后，由 Agent 按 SKILL.md **继续做完**：

1. 检查本机环境与已有 Vault；没有指定位置时使用用户 `Documents/个人知识库`。
2. 检测 Obsidian；未安装时主动从官方来源下载、校验并完成安装，不只给一个下载链接。
3. 建立六类知识库结构、项目卡等五类模板、工作台和 Obsidian 基础配置。
4. 在当前宿主实际发现的技能目录生成 `personal-kb`，或在支持的持久指令入口记录真实库路径。
5. 首次把已建目录作为 Obsidian Vault 打开，定位知识资产工作台，验证真实读写和检索。
6. 告诉用户实际路径、各阶段结果，以及以后直接说什么即可使用。

有桌面工具就代操作安装器和文件选择器。系统必须本人确认或实际能力缺失时，只交接那一个步骤，继续完成其余工作；不要把远程容器当作用户电脑，也不要声称未验证的阶段已完成。

保留用户笔记，已有相关配置先备份后小范围更新，不上传个人资料、不购买服务、不自动同步。
