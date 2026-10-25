# 姜胡说知识库安装 Skill

把一套能被 AI Agent 实际读写的个人知识库，装到你自己的目录里。

这是受姜胡说知识管理思路启发、结合 PARA 整理的适配版，**不是官方模板**。提供空白目录、模板、协作规则和离线安装器，不含私人笔记或付费课程。

## 直接交给 Agent

复制下面这段话给支持文件读写的 Agent：

> 请从 https://github.com/hanyh56/jianghushuo-kb-setup 下载完整仓库，读取根目录 SKILL.md，把这套知识库安装到我指定的目录，并接入你实际支持的指令入口。保留已有文件，遇到冲突先读原文再处理，安装后验证并告诉我路径。没有 skill 机制也可以直接按说明执行。

需要一个纯文本入口时，交给 Agent 这个 [安装说明](https://raw.githubusercontent.com/hanyh56/jianghushuo-kb-setup/main/INSTALL.md)。它会指向完整仓库，不能只下载 SKILL.md 而遗漏模板和脚本。

## 直接下载

[下载完整 ZIP 安装包](https://github.com/hanyh56/jianghushuo-kb-setup/archive/refs/heads/main.zip)

解压后，把 `jianghushuo-kb-setup-main` 重命名为 `jianghushuo-kb-setup`，整体放入你的 Agent 实际配置的 skills 目录。没有 skills 目录的 Agent，直接让它读取包里的 `SKILL.md`。

也可以克隆：

```sh
git clone https://github.com/hanyh56/jianghushuo-kb-setup.git
cd jianghushuo-kb-setup
```

## 会安装什么

```text
个人知识库/
├── 开始这里.md
├── 知识资产工作台.md
├── AGENTS.md
├── 00-灵感与收件箱/
├── 01-Projects-当前任务/
├── 02-Areas-长期领域/
├── 03-Resources-参考资料/
├── 04-Archive-归档/
├── 05-Skills-经验复利/
└── 90-系统/
    ├── 维护与AI协作规则.md
    ├── Agent接入说明.md
    ├── 模板/                    # 灵感、项目、知识卡、经验工作流、每日进度
    └── 知识库看板.base          # 可选的 Obsidian Bases 视图
```

平时从真实问题进入：灵感随手记，项目写实际动作和下一步，方法复用后再补证据。本人原话、外部观点、推测和 AI 建议分别记录。

`05-Skills-经验复利/` 保存经验笔记，安装它不会自动把每篇笔记注册成 Agent 技能。

## 手动安装知识库

需要 Python 3.8 或更高版本，只使用标准库，无需 pip、账号或网络。把下面的路径替换成你的实际保存位置：

```sh
python3 scripts/install.py --vault "/你的保存目录/个人知识库" --dry-run
python3 scripts/install.py --vault "/你的保存目录/个人知识库"
python3 scripts/install.py --vault "/你的保存目录/个人知识库" --check
```

Windows 可把 `python3` 换成 `py -3`。没有 Python 时，也可以让 Agent 按相对路径复制 `assets/vault/` 中缺失的文件。

如果你的宿主支持某个项目指令文件，可追加实际入口路径：

```sh
python3 scripts/install.py --vault "/你的保存目录/个人知识库" --agent-file "/你的Agent工作区/AGENTS.md"
```

`--agent-file` 也可指向宿主实际读取的 `CLAUDE.md` 等 UTF-8 指令文件；不要猜测不支持的配置位置。它只追加有标记的入口，保留原有内容。要检查接入，给 `--check` 命令传入相同的 `--agent-file`。

## 已有内容怎么处理

安装器只添加缺失文件。重复安装不会追加重复入口；内容不同的同名文件保留并列入 `conflicts`，由 Agent 读原文后合并。安装不搬迁旧笔记，不修改 `.obsidian` 设置，也不创建自动同步或定时任务。

安装完成后，要让 Agent **实际读一次**知识资产工作台和协作规则。当前会话能访问、其他会话自动加载、方法产生效果，需要分别验证。

## 验证范围

已在本地 macOS / Python 3.9 环境验证：换目录解压安装、中文和空格路径、重复安装、已有指令逐字节保留、文件冲突保护、缺失文件修复、静态链接和符号链接冲突拦截。

其他操作系统和各 Agent 产品的自动发现机制尚未逐一实测；核心文件为通用 Markdown，安装器不依赖特定 Agent API。
