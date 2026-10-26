# Obsidian 桌面落地

`desktop.py doctor` 只读取本机应用位置与 Vault 登记文件，帮助定位；不会上传本地路径、注册账号或改用户全局登记。`install` 会使用官方稳定版 metadata 和下载地址，校验 SHA-256 后安装或打开官方安装器。

## macOS

优先复用 `/Applications/Obsidian.app` 或用户 `Applications/Obsidian.app`。缺失时下载官方 Universal DMG，挂载为只读，验证应用代码签名，复制到用户 Applications 后卸载镜像。无需替换已有应用。首次系统确认使用当前桌面工具处理；系统要求本人确认时再由本人操作。

## Windows

下载官方 Universal EXE 后打开安装器；继续用桌面工具完成安装选项。没有可靠桌面工具时，请用户完成安装器这一步，随后重新检测。不要虚构静默安装参数，也不把启动安装器当作安装完成。

## Linux

优先使用已存在的 Obsidian 命令、AppImage 或 Flatpak。没有时按 CPU 架构下载官方 AppImage，保存到用户 `.local/opt/obsidian/Obsidian.AppImage` 并授予本文件执行权限。若 FUSE/桌面环境不满足，按官方说明处理依赖或安装方式；不擅自禁用 sandbox，也不在无桌面容器中声称 GUI 已完成。

## 第一次打开本库

1. 安装器先建立 `.obsidian/` 基础设置与完整知识库结构。
2. `desktop.py open --vault "准确路径"` 对已登记的库生成 URI，打开工作台；未登记时打开 Vault 管理器。
3. 在“Open folder as vault / 打开文件夹作为仓库”中选择步骤 1 的目录。此时已有文件和 `.obsidian` 目录，不需要再创建新库。
4. 再运行 `open`，查看知识资产工作台，确认六类目录、模板和动态表格。只有实际界面证据才能确认“已打开”。

Obsidian 的 `open?path=` 只能在它已知的 Vault 中定位文件，不能用来登记新库，也不能仅凭 URI 发送成功证明已注册。`setup.py` 会显式返回 `needs_vault_registration` 等阶段与下一步，Agent 必须完成目录选择后再恢复正常安装流程。

## Windows 的 Vault not found 恢复

关闭错误框，确认实际文件夹与工作台存在；保留已有文件，不重新建一层库。运行 `desktop.py open --vault "准确现有路径" --recover-vault-not-found` 强制打开 Vault 管理器，在“打开本地仓库 / Open folder as vault”中选中该目录并打开。随后不带恢复标记重跑 `setup.py`，重新读取登记并用 Vault ID 打开工作台；不再发送 `open?path=` 试图注册。

Windows 比较登记路径时按 Windows 规则处理大小写和正反斜杠，仍要求准确同一个目录，不把父目录或同名近似目录误认作本库。登记文件无法读取时报告 `needs_registry_check` 并回到管理器，不能把未知状态当成成功。

如果恢复后仍出现同一错误，停止重复 URI，检查运行的用户、Obsidian 实例与实际文件夹，在应用内选择工作台。只在真正缺少桌面能力时交接用户；不能直接编辑全局登记文件来制造成功状态。

使用中的旧库修改设置后可能需要重新加载；不覆盖用户的窗口布局、主题、快捷键或第三方插件配置。

来源（2026-10-26 核对）：[官方下载](https://obsidian.md/download)、[官方安装说明](https://help.obsidian.md/install)、[管理 Vault](https://help.obsidian.md/Files+and+folders/Manage+vaults)、[Obsidian URI](https://help.obsidian.md/uri)、[官方发行仓库](https://github.com/obsidianmd/obsidian-releases)。
