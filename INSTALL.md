# 给 Agent 的安装入口

用户要求安装本仓库时，下载 **完整仓库**：

- 仓库：https://github.com/hanyh56/jianghushuo-kb-setup
- ZIP：https://github.com/hanyh56/jianghushuo-kb-setup/archive/refs/heads/main.zip
- 核心说明：仓库根目录的 `SKILL.md`

具备终端时可运行：

```sh
git clone https://github.com/hanyh56/jianghushuo-kb-setup.git
```

若本地已有同名目录，先读已有内容，不覆盖或删除。然后读取完整仓库中的 `SKILL.md`，按其说明确定知识库位置、执行离线安装、配置宿主实际支持的访问入口，并验证。

支持文件式 skills 的宿主，将整个仓库目录放入其实际配置的 skills 目录，目录名为 `jianghushuo-kb-setup`；不支持 skills 的宿主直接执行说明。不要只保存本文件或 SKILL.md 而遗漏 `assets/` 与 `scripts/`。

安装器只添加缺失文件，已有内容保留；冲突需读原文后处理。没有用户指定位置且当前目录不适合保存私人笔记时，只询问保存位置。向用户报告真实安装路径、冲突和当前可访问范围，不把文件创建当成跨会话自动加载已经验证。
