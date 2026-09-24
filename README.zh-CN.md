# ONScripter PSP

[English](README.md) | 简体中文 | [日本語](README.ja.md)

面向 PSP 的 ONScripter 开发项目，目标是支持原生 **480×272** 显示和 **480×270（270p）** 游戏。最初的源码快照来自美少女万华镜2.5移植项目。本仓库包含引擎、对依赖库的本地修改及回归测试，**不包含游戏本体**，也不包含剧本、美术、音频、字体、存档或 ISO。

## 项目状态与参与贡献

**目前是早期开发快照，还不是可直接用于任意游戏的通用引擎。** 引擎从 `;$V4000G1500S480,272` 或 `;$V4000G1500S480,270` 等脚本头读取脚本原生尺寸。480×270 脚本头解析已有主机端回归测试，但其在 PSP 实机上的显示位置和渲染效果仍需专项验证。

本项目在开发、调试、测试和文档编写中**使用生成式人工智能（GenAI）**。生成的代码可能存在错误。欢迎任何人通过 Issue、代码审查、修复、测试、文档和 Pull Request 改进项目。反馈时请提供可复现的步骤，并区分 PSP 实机与模拟器上的结果。

可复用的辅助模块现已按功能命名：`PSPSavedata.h`（路径映射与带错误检查的写入）、`PSPSavedataDescription.h`（SFO 描述更新）、`ONSSaveText.h`（文本转换）、`PSPSavedataMac.h`（mode-1 完整性校验）和 `ONSMaskGain.h`（遮罩转场）。这些文件都不是无用的游戏素材。

请为每个游戏使用独立标识进行构建，例如 `make -f Makefile.PSP GAME_ID=TEST00001 PSP_EBOOT_TITLE="My Game"`。标识格式为四个大写字母加五位数字。这里的 `ONSP00001` 仅供引擎开发使用，不应由多个发行游戏共用。切换标识或编码前，请先运行 `make -f Makefile.PSP clean`，因为 make 的依赖关系不会跟踪编译选项的变化。

通用化尚未完成：当前存档适配层支持八个存档位，需要配套的 `ui/savedata/{CFG,01..08}.SFO` 模板，以及 `ICON_SYSTEM.PNG`、`ICON0.PNG` 和 `PIC1.PNG`；描述更新代码还依赖旧版固定 SFO 布局。修改 GAME_ID 不会生成或更新这些模板，模板中内嵌的存档目录标识必须与构建配置一致。默认编码仍为 CP936（`ONS_CN_CP936`）。通用元数据生成及更多存档位支持属于后续工作。原移植项目已验收的游戏发行版保持不变。

## 主要改动

- 原生 480×272 脚本布局和 CP936 文本支持。
- PSP PMF 播放与 GPU 集成、语音缓冲区生命周期改进及背景缓存。
- 可配置游戏标识的 PSP 存档集成、对话控制和诊断日志。
- 光盘启动目录为 `disc0:/PSP_GAME/USRDIR`；光盘模式的诊断日志写入 `ms0:/PSP/<GAME_ID>_ISO.log`。

源码保留了经过实机测试的构建中的诊断功能。用户反馈，在 PSP03g、6.20 PRO-C2 / Inferno 环境中，启动、同次运行内读档和重启游戏后读档均正常。这不代表所有 PSP 型号均已验证，也不代表完成了实机全流程测试。构建会申请扩展内存，目前不支持 PSP-1000。

## 构建

需要 PSPSDK、PSP SDL 1.2 及其图像、混音和字体依赖。已验证的构建环境为以下固定版本的 PSPDEV 容器。在 Linux shell 中进入仓库目录后执行；也可使用 WSL，并将仓库放在其可访问的挂载盘上：

```sh
docker run --rm -v "$PWD:/src" -w /src \
  pspdev/pspdev@sha256:b22811072ea0721d7f6c666a5a279b6def2b0cd95892b819d9570f8ffc4452c0 \
  sh -c 'make -f Makefile.PSP -j4'
```

输出为 `EBOOT.PBP` 和 `onscripter.elf`。PBP 仅含基本开发用元数据，不含游戏美术。请自行提供合法取得且兼容的游戏数据；本仓库本身不能重新生成已发行的游戏 ISO。Makefile 会从源码构建随仓库提供的依赖库修改版本。

构建完成后，运行 `python -m unittest discover -s tests`。测试需要 Python 3；需要编译的主机端测试程序还依赖各自指定的主机编译器，部分测试使用 Windows Visual Studio 2022 Community。CP936 测试输入由程序生成，并非从游戏中复制；依赖私有工作区的导入修正测试未纳入仓库。实机测试与此测试集相互独立。

光盘打包方面，已验收的游戏使用了 `genisoimage -xa -iso-level 3 -allow-lowercase -allow-multidot -omit-version-number`。非 XA 镜像曾在测试用 PSP 上导致部分文件无法打开。由引擎直接打开的视频及支持文件应保留在 NSA 归档之外。

## 移植工具

[资源与视频准备指南（英文）](docs/asset-preparation.md)介绍声明画布、旧式透明度布局、脚本状态隔离及媒体验证。`tools/pmf_prepare.py` 提供基于时间戳的时长规划，以及针对特定 Mps2Pmf 格式的结束时间戳修正和输入检查。测试使用合成数据，仅依赖 Python 标准库。这些是主机端辅助工具，不是新增运行时功能、内置编码器或完整游戏转换器。

## 来源与致谢

- Ogapee 开发的原版 [ONScripter](https://onscripter.osdn.jp/)，保留原始版权声明。
- 直接代码基础：[PSP-Archive/ONScripter-for-PSP](https://github.com/PSP-Archive/ONScripter-for-PSP)，版本 `ddc2d04a17a2db09bc770bee61578ba04e1eed25`。
- [PSPDEV](https://github.com/pspdev)：工具链、PSP SDL 及 [libpspav](https://github.com/pspdev/libpspav)。
- [Xiph Tremor](https://gitlab.xiph.org/xiph/tremor) 和 [tiny-AES-c](https://github.com/kokke/tiny-AES-c)。

依赖库来源详见 [THIRD_PARTY.md](THIRD_PARTY.md) 及随附声明。相关项目：[ONScripterYuri](https://github.com/YuriSizuku/OnscripterYuri) 和 [ONScripter-Jh](https://github.com/jh10001/ONScripter-Jh)。这些是参考项目，不表示本快照由其派生或已包含其代码。

## 测试反馈

请提供 PSP 型号、固件与 ISO 驱动、操作步骤、预期行为和实际行为，并尽可能附上诊断日志。上传前请检查日志，其中可能包含文件路径和游戏过程信息。请勿在公开 Issue 中附上受版权保护的游戏文件或个人存档。

## 许可证

基于 ONScripter 的引擎采用 **GPL-2.0-or-later**，详见 [COPYING](COPYING) 和各文件中的声明。随附第三方组件保留各自的许可证。本快照中修改过的引擎文件包含上述 PSP/Biman 适配，且保留上游作者声明。

维护者希望本项目不被用于商业牟利。**这只是不具有约束力的意愿，并非额外的许可证限制。** GPL 赋予的权利（包括商业使用）保持不变。引擎许可证不授予任何独立受版权保护的游戏素材的使用权。
