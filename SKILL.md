---
name: jianghushuo-kb-setup
description: 从零落地姜胡说思路的个人知识库：安装 Obsidian、建立六类目录和模板、配置 Agent 持久入口、打开工作台并验证读写。用户要求安装或补齐这套知识库时使用。
---

# 把个人知识库真正落地

默认交付“Agent 能用、Obsidian 能打开、目录与模板已搭好”的完整本地工作流。随包是通用空白模板和 Python 标准库工具，不含个人笔记、账号或付费课程。这是受姜胡说思路启发的适配版，不是官方模板。

## 执行原则

- 用户执行本 skill 即是在请求完成这套安装；在已有授权内直接推进，不把每个普通步骤变成选择题。系统要求的权限、安装器确认和真正的路径冲突仍按实际情况处理。
- 新用户不必自己安装依赖、手填路径或先设计分类。默认使用本机用户的 `Documents/个人知识库`；用户已指定路径或已有同一套库时沿用它。
- 不把“任意 Agent”理解成任意聊天窗口都有本机权限。先确认当前是用户本地桌面、远程容器还是纯聊天。纯聊天无法创建本地文件；远程环境不要冒充用户电脑，把文件层交付和本机桌面步骤分别说明。
- 只安装免费桌面软件与本包内容，不要求账号、购买同步服务、第三方插件或全库上传。下载 Obsidian 时使用官方来源。

## 1. 检查环境与定位

读取本包文件，确认 `scripts/` 和 `assets/` 完整。脚本从任意 cwd 都能运行，但命令中的脚本路径要指向本 skill 的实际位置。

```sh
python3 scripts/desktop.py doctor
```

Windows 优先使用可用的 `py -3`，否则探测 `python`；脚本需要 Python 3.8+，不需要 pip。没有 Python 不必为本包装依赖，按 [references/no-python.md](references/no-python.md) 用本机文件工具和官方图形安装器完成相同结果，不停在“请先装 Python”。

`doctor` 返回系统、已安装应用、已登记 Vault 与建议路径。已有同结构库优先沿用；有多个无法判断的库，才用一个自然语言问题确认目标。没有现有库则直接使用默认目录。不要把个人知识库建进临时目录、skill 目录或公司代码仓库。

识别当前宿主的**真实 skills 发现目录**。优先沿用已成功加载本 skill 的个人 skills 根目录；不要把临时下载目录当成发现目录。Codex / Claude Code 的已核实路径和其他宿主处理方式见 [references/agent-hosts.md](references/agent-hosts.md)。

## 2. 检测并安装 Obsidian

未安装时主动完成这一步：

```sh
python3 scripts/desktop.py install
```

已有 Obsidian 则复用，不升级或重装。辅助脚本读取官方稳定发行版，匹配系统与架构，校验官方 SHA-256；macOS 安装到用户 Applications，Linux 使用用户目录 AppImage，Windows 启动官方安装器。

Windows 返回 `installer_launched_finish_in_gui` 时，继续用可用的桌面工具完成安装器；系统必须本人处理的确认才交给用户。完成后重跑 `doctor`，不能把“安装器已打开”当成应用已安装。脚本下载或签名校验失败时检查一次具体原因，必要时改走 [官方下载页](https://obsidian.md/download) 的图形安装流程，不绕过校验或关闭系统保护。操作说明见 [references/obsidian-desktop.md](references/obsidian-desktop.md)。

无桌面环境、或用户明确只需要 Agent 文件层时，不强行安装桌面应用；继续搭建文件与接入，保留桌面待办并准确报告。

## 3. 建库、配置模板和 Agent 入口

新用户本地运行可直接使用默认目录。把 `--skills-dir` 换成步骤 1 确认的宿主目录：

```sh
python3 scripts/install.py --skills-dir "/actual/host/skills" --dry-run
python3 scripts/install.py --skills-dir "/actual/host/skills"
```

有明确 Vault 路径时追加 `--vault "/actual/path/个人知识库"`。已确认是使用标准个人目录的 Codex / Claude Code，也可分别用 `--agent codex` / `--agent claude`。不要把当前宿主臆测成其中一种。

安装器完成这些事：

- 建立收件箱、当前任务、长期领域、参考资料、归档、经验复利，以及系统目录、工作台和五类模板。
- 配置 Obsidian 内置模板、日记、Bases、新笔记默认收件箱、移动文件自动更新链接；修改已有相关配置前逐字节备份，保留无关设置。
- 在实际 skills 目录生成 `personal-kb/SKILL.md`，写入这个人的真实知识库路径，使以后的知识库请求有独立入口。
- 临时新建一条明确标为测试的笔记，写入、回读、检索并删除，不把测试记成用户经历。

不支持 skills、但支持持久指令文件的宿主，使用 `--agent-file "/actual/host/AGENTS.md"` 或实际读取的 `CLAUDE.md`。原指令保留。两种机制都没有时，在当前会话读取规则，并明确持久接入尚未建立；不要声称下次自动可用。

已有笔记不覆盖。旧版原封未动的模板可以依据随包已知校验值备份升级；用户改过的同名文件列入 `conflicts`，读原文后只合并本次必要部分。不要跳过冲突直接宣布完成，也不要把建库扩大为搬迁用户全库。

## 4. 在 Obsidian 注册并打开这一个库

```sh
python3 scripts/desktop.py open --vault "/actual/path/个人知识库"
```

若返回 `needs_vault_registration`，它打开的是 Vault 管理器。继续用桌面工具点“Open folder as vault / 打开文件夹作为仓库”，选择输出中的准确目录；不要点“新建库”而再建一层空库。若没有桌面操作能力，只把这一个不可代操作的步骤交给用户。

注册后重跑 `open`，它会定位到“知识资产工作台”。用当前可用的桌面工具确认工作台、目录和动态视图可见；首次没有项目时列表为空是正常的。命令发出不等于窗口正确打开。不要直接改全局 `obsidian.json` 来伪造注册成功。

## 5. 验收与交付

```sh
python3 scripts/install.py --vault "/actual/path/个人知识库" --skills-dir "/actual/host/skills" --check
```

使用了其他接入参数时，检查时传相同参数。实际读取库内 `AGENTS.md`、`知识资产工作台.md`、`90-系统/维护与AI协作规则.md` 和生成的 `personal-kb/SKILL.md`。检查目录、模板、设置、来源链接、临时读写验收和持久入口，处理未解决项。

分别报告：知识库与读写是否就绪、Agent 入口是否配置、Obsidian 是否安装、本库是否登记并打开。没有真实证据的阶段保留“待完成/待验证”，不要用一个成功状态覆盖所有阶段。新会话的自动发现取决于宿主；按需刷新 skills，给出“我的知识库在哪”这一句后续验证提示，不声称本会话已经证明另一会话的行为。

完成后告诉用户真实路径，以及可以直接说“把这个想法记入知识库”或“为这件事建项目卡”。无需补齐资料，不强制每日整理；无真实项目时不编造示例项目。日常使用由 `personal-kb` 接续，不要每次重新安装。
