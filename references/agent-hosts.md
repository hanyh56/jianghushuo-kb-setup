# 接入当前 Agent

先确认宿主身份与实际 skills 根目录，不按磁盘上“有某个目录”推断当前运行的是哪个产品。当前安装 skill 已被成功发现时，优先沿用它的个人 skills 根目录。下载缓存和临时解压目录不算发现目录。

| 宿主 | 常见个人 skills 目录 | 安装参数 |
| --- | --- | --- |
| Codex 本地 | `~/.agents/skills/`；已确认当前宿主加载其他配置目录时沿用实际目录 | `--agent codex`，或显式 `--skills-dir` |
| Claude Code 本地 | `~/.claude/skills/` | `--agent claude`，或显式 `--skills-dir` |
| 其他支持 Agent Skills 的本地宿主 | 读取其已配置目录或官方说明 | `--skills-dir "真实路径"` |
| 只有项目指令文件的宿主 | 实际读取的 `AGENTS.md`、`CLAUDE.md` 或其他 UTF-8 文件 | `--agent-file "真实路径"` |

`--skills-dir` 优先于 `--agent` 的标准目录。安装器只生成一个 `personal-kb` 运行 skill，不复制用户笔记到 skills 目录，不把本库经验笔记自动注册为可执行 skill。

当前宿主限制了库目录的访问时，使用其支持的添加目录或权限流程；skills 被发现不等于已获得文件访问权。只改本次需要的入口，不替换全局规则，不把含私人路径的配置提交到公共仓库。

Codex 可以按需刷新或重开会话。Claude Code 的个人本地 skills 不等于 Cowork 或云端会话的 skills；远程容器的路径也不等于用户本机路径。

如果已有 `personal-kb` 指向另一个 Vault，保留并确认用户的目标，不悄悄更换。若实际需要多库，再为每库单独命名运行入口。

来源（2026-10-26 核对）：[OpenAI 官方 Build skills](https://learn.chatgpt.com/docs/build-skills)、[Claude Code 官方 Skills](https://code.claude.com/docs/en/skills)。路径与限制若变化，以宿主实际发现结果和最新官方说明为准。
