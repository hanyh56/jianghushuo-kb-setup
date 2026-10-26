# 姜胡说知识库安装 Skill

打开一个本地 Agent，执行这个 skill，让它从零把 **Obsidian、知识库结构、模板、Agent 入口和首次使用验收**一起落地。

这是受姜胡说知识管理思路启发、结合 PARA 整理的适配版，**不是官方模板**。不含私人笔记或付费课程，不要求购买同步服务或注册账号。

## 给 Agent 这一句话

> 请按 https://raw.githubusercontent.com/hanyh56/jianghushuo-kb-setup/main/INSTALL.md 完整安装这套知识库，包括检查和安装 Obsidian、搭建目录与模板、配置后续 Agent 入口、打开工作台并验证读写。已有内容保留。

具备链接读取、文件下载和本机执行能力的 Agent 可获取完整仓库并执行。没有现有库和指定路径时，默认建在当前用户的 `Documents/个人知识库`，不要求你先设计分类或填写安装参数。

[下载完整 ZIP](https://github.com/hanyh56/jianghushuo-kb-setup/archive/refs/heads/main.zip) · [查看 Skill](SKILL.md)

## WorkBuddy 安装方式

本 skill 已发布在 GitHub，尚未由维护者上架到 SkillHub 或 ClawHub。只说「安装 jianghushuo-kb-setup」，WorkBuddy 可能只搜索市场而找不到。

按 [WorkBuddy 官方说明](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)，普通对话安装仅支持市场技能，自定义技能包需要上传导入：

1. 下载上面的完整 ZIP。
2. 在 WorkBuddy 打开「专家·技能·连接器」→「技能」→「添加技能」→「上传技能」，选中 ZIP。
3. 在「已安装」中确认 `jianghushuo-kb-setup` 已启用。若当前版本不接受 GitHub ZIP 的外层目录，将解压后的完整技能目录重新打包再上传；保留全部配套文件。
4. 输入：

   > 使用 jianghushuo-kb-setup，完整安装我的 Obsidian 个人知识库，搭好目录、模板和工作台，配置后续使用入口，并完成读写验收。已有内容保留。

这里确认的是官方提供自定义技能导入方式；维护者尚未在实际 WorkBuddy 客户端完成端到端验收。导入成功、知识库搭建、应用打开和后续会话入口需按实际结果分别确认。

## 一次安装会完成什么

1. **检查环境**：识别系统、Python、Obsidian、已登记的库和当前 Agent 的真实技能目录。
2. **安装 Obsidian**：已有则复用；未安装时匹配官方稳定版与系统架构，下载并验证 SHA-256，再安装或完成官方安装器。
3. **搭建知识库**：建立六类目录、工作台、五类模板和首次使用入口。
4. **配置界面**：启用内置模板、日记和 Bases；新笔记进入收件箱，移动文件更新链接。已有相关配置先备份，无关设置保留。
5. **接入后续 Agent**：生成带真实库路径的 `personal-kb` 使用 skill；仅支持指令文件的宿主则追加入口。
6. **打开并验收**：首次将目录作为 Vault 登记，定位工作台；写入、回读、检索并清理临时测试笔记。

安装器已打开、应用已安装、本库已登记、工作台已显示，是四个不同状态。Agent 必须按实际证据完成并报告，不能只生成目录就称全部完成。

## 知识库结构

```text
个人知识库/
├── AGENTS.md
├── 第一次使用.md
├── 开始这里.md
├── 知识资产工作台.md
├── 00-灵感与收件箱/
├── 01-Projects-当前任务/
│   └── 待确认是否继续/
├── 02-Areas-长期领域/
│   └── 每日记录/
├── 03-Resources-参考资料/
│   ├── 本人原始记录/来源导入/
│   └── 外部参考/
├── 04-Archive-归档/
├── 05-Skills-经验复利/
│   └── 待验证方法/
├── 90-系统/
│   ├── 模板/
│   ├── 知识库看板.base
│   └── 维护与AI协作规则.md
└── .obsidian/                 # 库内基础配置
```

经验目录里的笔记和 Agent 技能是不同的东西：`05-Skills-经验复利/` 保存方法与证据；宿主 skills 目录中的 `personal-kb` 告诉 Agent 如何找到并使用你的库。

## 装完怎么用

直接说：

- “把这个想法记入我的知识库：……”
- “我要做这件事，帮我建项目卡：……”
- “找一下我以前关于……的记录。”

新会话可说“我的知识库在哪”验证入口。没有真实项目时不创建假项目，不要求每天清空收件箱，不把 AI 建议写成你的经历。

## 手动运行

脚本使用 Python 3.8+ 标准库，无需 pip。知识库文件安装可离线完成；缺少 Obsidian 时需要联网下载。没有 Python 的 Agent 可直接按[文件工具方案](references/no-python.md)完成，不必额外安装依赖。

```sh
git clone https://github.com/hanyh56/jianghushuo-kb-setup.git
cd jianghushuo-kb-setup
python3 scripts/desktop.py doctor
python3 scripts/desktop.py install
```

确认宿主后，下面二选一；其他宿主用 `--skills-dir "它实际读取的目录"`：

```sh
python3 scripts/install.py --agent codex
python3 scripts/install.py --agent claude
```

自定义知识库位置追加 `--vault "实际路径"`。Windows 可使用 `py -3`。

```sh
python3 scripts/desktop.py open --vault "实际知识库路径"
python3 scripts/install.py --vault "实际知识库路径" --skills-dir "实际技能目录" --check
```

首次打开会进入 Vault 管理器，选择“打开文件夹作为仓库”，选中输出的准确目录，然后再运行 `open`。执行 skill 时，这一步由具备桌面工具的 Agent 代操作；系统必须本人确认、或者 Agent 没有桌面控制能力时，才需要本人完成该步骤。

## 已有内容与升级

用户笔记保留，同名不同内容会报告冲突。旧版原封未动的包内模板可按已知校验值备份升级；改过的笔记需要先读再合并。Obsidian 配置只更新本包需要的字段，原文件逐字节备份；主题、窗口布局和其他插件设置保留。

重复运行不会重复写入口、制造测试笔记或重新安装已有 Obsidian。不自动搬迁旧笔记、上传全库、恢复同步或创建定时任务。

## 环境边界和验证

完整本地体验需要持久文件、桌面系统和相应操作权限。远程容器可搭好文件层，但不能替用户本机安装或打开应用；纯聊天窗口不能创建本地文件。Agent 会明确报告还缺的实际能力，不能把这些阶段标成完成。

运行自动检查：

```sh
python3 -m unittest discover -s tests -v
```

维护者修改 `assets/vault/` 后，先运行 `python3 scripts/build_manifest.py` 更新无 Python 安装用的文件清单，再运行测试。

仓库包含 macOS、Windows、Linux 的测试工作流。自动检查覆盖安装、重复执行、配置备份、旧版模板升级、用户文件保护、持久入口、下载校验和首次 Vault 登记状态。应用安装器的真人/桌面交互与不同产品的新会话发现机制，按实际环境分别验收。

更多接入细节：[Agent 宿主](references/agent-hosts.md) · [Obsidian 桌面流程及官方来源](references/obsidian-desktop.md)。
