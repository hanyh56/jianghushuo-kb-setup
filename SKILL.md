---
name: jianghushuo-kb-setup
description: 从零完整安装 Obsidian 个人知识库，自动获取完整技能包、安装当前 Agent 入口、建目录与模板、登记 Vault 并验收读写；修复首次打开时的 Vault not found。用户要求安装、更新或补齐这套知识库时使用。
---

# 把个人知识库完整落地

用户说“安装并执行这个 skill”或“使用 jianghushuo-kb-setup”，即请求执行以下完整流程，不需要再在外部提示词列要求。默认交付 skill 已安装启用、Obsidian 可用、知识库与后续 Agent 入口已建立、工作台已打开且读写通过；仅系统必须本人确认、真正的目标冲突或缺少实际能力时交接对应步骤，其余工作继续完成。

随包是空白模板和 Python 标准库工具，受姜胡说思路与 PARA 启发，不是官方模板，不含个人笔记或付费课程。保留用户已有内容与设置，不上传个人资料、不购买服务、不自动同步，不创建虚构项目或经历。

## 0. 获取完整包并安装当前 skill

发布来源是 https://github.com/hanyh56/jianghushuo-kb-setup ，完整 ZIP 是 https://github.com/hanyh56/jianghushuo-kb-setup/archive/refs/heads/main.zip 。维护者尚未上架 SkillHub / ClawHub；不要因为市场搜索无结果而停止或安装近似名称的包。

如果当前只有 INSTALL.md / SKILL.md 或附件缺失，用 Git 或本机下载工具获取并解压完整包，保留 `assets/`、`scripts/`、`references/`。读取下载后的本文件，核对 `assets/vault-manifest.json`；不要在缓存中仅存一份说明就称 skill 已安装。

确认当前是用户电脑、远程环境还是纯聊天，以及宿主真正读取的 skills 目录。优先沿用已成功加载本 skill 的个人技能根目录；下载目录不算发现目录。宿主差异见 [references/agent-hosts.md](references/agent-hosts.md)。WorkBuddy 需要上传时，由可用界面工具导入完整包并确认「已安装」中已启用；只能本人操作时，准备好包并只交接该步骤。其他本地宿主由下方 `setup.py --skills-dir` 将完整安装 skill 放入真实目录。单纯有文件不代表宿主已启用。

用户请求更新时，先取得新版完整包，从新版目录运行 `--update-skill`，只更新同名安装 skill 并逐文件备份；不通过更新 skill 迁移或覆盖个人笔记。没有原生 skills 机制但有持久指令文件时用 `--agent-file`，如实说明本宿主的接入方式。

## 1. 检查本机与实际知识库

```sh
python3 scripts/desktop.py doctor
```

脚本路径指向本 skill 的真实位置。Windows 使用可用的 `py -3` 或 `python`；需要 Python 3.8+ 标准库，不需要 pip。没有 Python 时按 [references/no-python.md](references/no-python.md) 用现有文件与桌面工具完成相同流程，不要求用户先装开发依赖。

复用用户指定或已确认的同一套知识库；检查 `doctor` 的已登记库与已有 `personal-kb` 真实路径，避免重复建库。确有多个目标无法判定才询问。新用户默认使用本机当前用户的 `Documents/个人知识库`，不要照抄别人的 `C:\Users\Administrator`、放入公司代码、技能目录或临时目录。

远程容器不能替本机安装或打开应用；纯聊天没有本机文件权限时，指出实际缺少的能力。不要把远程文件当作用户电脑的落地结果。

## 2. 执行统一安装入口

确认宿主目录后，使用统一入口，不自行拼接打开 Obsidian 的 URI：

```sh
python3 scripts/setup.py --skills-dir "/actual/host/skills"
```

已有库追加 `--vault "/actual/path/个人知识库"`。已确认使用标准目录的 Codex / Claude Code 可分别用 `--agent codex` / `--agent claude`。只有持久指令文件的宿主用 `--agent-file "/actual/host/AGENTS.md"` 或实际读取的文件。更新安装 skill 时追加 `--update-skill`，原文件字节会备份。

此入口检查完整包和冲突、安装当前 skill、建立六类目录与五类模板、合并 Obsidian 内置设置、生成绑定真实库路径的 `personal-kb`、写入回读并检索临时测试笔记、检测或安装官方 Obsidian，再按登记状态打开管理器或工作台。已有内容冲突会报告并保留；读原文后只合并必要部分，不跳过冲突声称完成。

读取 JSON 的 `pending_actions` 并继续执行。脚本退出码为 0 只表示程序执行完，`needs_actions` 和 `complete:false` 表示 Agent 仍有工作；它没有桌面视觉，不能自行证明安装启用、工作台显示或整个任务完成。

## 3. 处理应用安装与首次登记

- `finish_obsidian_installation`：按官方流程继续安装。Windows 返回 `installer_launched_finish_in_gui` 时使用桌面工具完成安装器，再重跑检测；不把安装器启动当作应用安装完成。下载或校验失败检查具体原因，必要时走 [官方下载页](https://obsidian.md/download)，不关闭系统保护。详见 [references/obsidian-desktop.md](references/obsidian-desktop.md)。
- `register_existing_folder_in_gui`：在 Obsidian 管理器选择 “Open folder as vault / 打开文件夹作为仓库 / 打开本地仓库”，在系统目录选择器中选中 `folder` 的准确现有目录并打开。不要点“新建库”再建一层。使用当前桌面工具代操作，只有确无操作能力时交接这一步。
- 完成界面操作后，以相同 Vault 与宿主参数重跑 `setup.py`，取得刚写入的登记状态，确认 `desktop.registered` 为 true，再查看工作台。若登记文件暂未更新，观察实际窗口后重新检测，不直接修改全局 `obsidian.json`。

### 已出现 Vault not found 时

这是必须恢复的步骤，不是成功提示。`obsidian://open?path=…` 只在已知库中查找笔记，**不能登记新的知识库**；也不要改斜杠或重复发送同一失败链接来冒充修复。

1. 用实际桌面工具关闭错误对话框；核实原知识库目录及 `知识资产工作台.md` 确实存在，复用它而不重建。
2. 运行恢复入口：

   ```sh
   python3 scripts/desktop.py open --vault "/actual/path/个人知识库" --recover-vault-not-found
   ```

3. 在管理器通过目录选择器完成上一段的“打开现有文件夹”。该恢复入口即使缓存显示已登记，也会强制返回管理器，避免重复旧错误。
4. 重跑正常 `setup.py`，**不带恢复标记**；登记成功后它使用 Vault ID 与编码后的工作台文件名打开。Windows 路径比较兼容大小写和正反斜杠。若仍报相同错误，停止重复 URI，检查当前 Obsidian 实例、用户与实际目录，在应用内手动选择工作台；保留未解决状态。

## 4. 验收并交付

```sh
python3 scripts/setup.py --vault "/actual/path/个人知识库" --skills-dir "/actual/host/skills" --check
```

使用原来的宿主参数。`--check` 只读，不下载、不写入、不启动应用。然后完成脚本不能代替的实际验收：

- 在宿主中确认安装 skill 已启用、`personal-kb` 已发现或持久指令确实有效；未确认不能声称新会话自动可用。
- 实际读取库内 `AGENTS.md`、`知识资产工作台.md`、`90-系统/维护与AI协作规则.md` 和绑定真实路径的运行入口。
- 检查脚本读写回读与检索通过，临时测试笔记已清理，模板与链接可用；没有 Python 则按替代流程做同样验收。
- 用实际界面确认正确库名、工作台、六类目录与动态列表。新库没有项目时，列表为空正常。界面报错就继续恢复，不把命令已发出、登记存在或窗口标题当作工作台已显示。

最终一次性交代：安装 skill 与知识库实际路径、skill 安装启用状态、后续 Agent 入口、Obsidian 安装状态、库登记及工作台显示、读写验收，以及尚未完成的具体一步和原因。没有证据的阶段保留待验证。

日常只需说“把这个想法记入知识库”“为这件事建项目卡”或“找以前关于……的记录”，由 `personal-kb` 接续，不反复安装。可以新开会话说“我的知识库在哪”验证后续发现；不要求每天清空收件箱或整理全库。
