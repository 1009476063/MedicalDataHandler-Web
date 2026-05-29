# MedVista 竞品分析报告

> 生成日期：2026-05-29

## 一、竞品概览

在 GitHub 上搜索到以下主要医学影像查看器竞品：

| 项目 | Stars | 语言 | 架构 | GitHub 地址 |
|------|-------|------|------|------------|
| **OHIF Viewers** | 4,183 | TypeScript | 浏览器端 + 扩展系统 | `ohif/viewers` |
| **DWV (DICOM Web Viewer)** | 1,819 | JavaScript | 纯客户端零安装 | `ivmartel/dwv` |
| **Weasis** | 1,256 | Java/Kotlin | 桌面应用 + Web | `nroduit/Weasis` |
| **Cornerstone3D** | 1,070 | TypeScript | WebGL 渲染引擎 | `cornerstonejs/cornerstone3D` |

---

## 二、核心差异对比

### 2.1 渲染技术

| 能力 | MedVista | OHIF | Cornerstone3D | DWV | Weasis |
|------|----------------------|------|---------------|-----|--------|
| 2D 切片查看 | Canvas 2D | WebGL | WebGL | Canvas 2D | Java Swing |
| 3D 体渲染 | 无 | 有 (MPR/MIP/VR) | 有 (GPU加速) | 无 | 有 |
| GPU 加速 | 无 | 有 | 有 (WebGL) | 无 | 有 |
| MPR 多平面重建 | 无 | 有 | 有 | 有(基础) | 有 |
| 窗宽窗位实时调节 | 支持 | 支持 | 支持 | 支持 | 支持 |

**差距分析**: 本项目使用 Canvas 2D 绘制，OHIF 和 Cornerstone3D 使用 WebGL 渲染，支持 GPU 加速的 3D 体渲染（MPR、MIP、VR）。这是最大的技术差距。

### 2.2 DICOM 支持范围

| SOP Class | MedVista | OHIF | Cornerstone3D | DWV | Weasis |
|-----------|----------------------|------|---------------|-----|--------|
| CT/MR/PT/NM 图像 | 有 | 有 | 有 | 有 | 有 |
| RT Structure | 有 | 有 (扩展) | 有 | 无 | 有 |
| RT Dose | 有 | 有 (扩展) | 有 | 无 | 有 |
| RT Plan | 有 (元数据) | 有 (扩展) | 有 | 无 | 有 |
| DICOM Segmentation | 无 | 有 | 有 | 无 | 有 |
| SR (结构化报告) | 无 | 有 | 有 | 无 | 有 |
| ECG | 无 | 无 | 无 | 无 | 有 |
| 4D 动态序列 | 无 | 有 | 有 | 无 | 有 |
| 多帧图像 | 无 | 有 | 有 | 有 | 有 |

**差距分析**: 本项目在 RT 支持方面已覆盖结构和剂量，但缺少 DICOM Segmentation（分割掩码）和 SR（结构化报告）支持。

### 2.3 系统架构

| 特性 | MedVista | OHIF | DWV | Weasis |
|------|----------------------|------|-----|--------|
| 架构模式 | 前后端分离 | 前端插件化 | 纯前端 | 客户端插件化 |
| 渲染引擎 | 自建 Canvas | Cornerstone3D | 自建 Canvas | Java 3D |
| 扩展机制 | 无 | 插件/模式系统 | npm 包 | OSGi 插件 |
| 数据存储 | 服务端 Session | DICOMweb/PACS | 纯本地 | 本地/DICOMweb |
| 协议支持 | HTTP 上传 | DICOMweb/WADO | HTTP 上传 | DICOMweb + DIMSE |
| PACS 集成 | 无 | 有 | 无 | 有 |
| 认证系统 | 无 | OpenID Connect | 无 | OAuth 2.0 |
| 国际化 | 中英双语 | 20+ 语言 | 多语言 | 20+ 语言 |
| FDA 合规 | 无 | 有 (部分产品) | 无 | 无 |

**差距分析**: OHIF 采用插件化架构，可灵活扩展；本项目是单体应用，功能扩展受限。本项目没有 PACS 集成能力，需要用户手动上传文件。

### 2.4 部署与分发

| 特性 | MedVista | OHIF | DWV | Weasis |
|------|----------------------|------|-----|--------|
| 部署方式 | Docker / 本地 | Docker / 静态托管 | npm 嵌入 | 安装包 / Web |
| 前端构建 | Vue 3 + Vite | React + Vite | 纯 JS | Java / WAB |
| 后端依赖 | Python FastAPI | 无 (纯前端) 或有 | 无 | Java Runtime |
| 安装复杂度 | 中等 | 低 | 极低 | 高 |
| 嵌入性 | 低 | 高 (可嵌入 React) | 高 (npm) | 中等 |

**差距分析**: DWV 和 OHIF 可以纯前端运行，不需要后端服务器。本项目强依赖 Python 后端处理 DICOM 解析和图像生成。

---

## 三、各竞品详细分析

### 3.1 OHIF Viewers (4,183★)

**优势**:
- 扩展/模式（Extension/Mode）架构，功能按需加载
- 底层使用 Cornerstone3D，GPU 加速渲染
- DICOMweb 原生支持，可直接连接 PACS
- 2D/3D/MPR/MIP/VR 完整查看能力
- RT 结构/剂量通过扩展支持
- 支持 DICOM Segmentation、4D 体积
- 测量工具（长度、角度、ROI 统计）
- OpenID Connect 认证
- FDA-cleared 产品（Mirth CloudConnect）

**劣势**:
- React 技术栈，与本项目 Vue 不兼容
- 纯前端架构，不提供 NIfTI 转换功能
- RT 支持需要安装额外扩展
- 配置复杂度高

### 3.2 DWV (1,819★)

**优势**:
- 零安装、零依赖的纯 JavaScript 库
- npm 包可嵌入任何前端项目
- 基础 MPR 支持
- 支持 DICOMweb 加载
- 轻量级，适合嵌入式场景

**劣势**:
- 不支持 RT/SR/ECG 等高级 SOP Class
- 无 3D 体渲染
- 无 GPU 加速
- 无 PACS 集成
- 无认证系统

### 3.3 Weasis (1,256★)

**优势**:
- 全面的 DICOM SOP Class 支持（包括 ECG）
- 完整的 RT 支持（结构、剂量、DVH 曲线）
- 3D 体积渲染
- DICOMweb + DIMSE 双协议支持
- OSGi 插件系统，高度可扩展
- 20+ 语言国际化
- OAuth 2.0 认证

**劣势**:
- Java 桌面应用，安装复杂
- 前端体验不如 Web 原生应用
- 社区活跃度不如 OHIF

### 3.4 Cornerstone3D (1,070★)

**优势**:
- WebGL 渲染引擎，GPU 加速
- 被 OHIF 采用为底层渲染库
- WebAssembly DICOM 解码
- 分割掩码叠加显示
- AI 集成接口
- 高性能大体积数据处理

**劣势**:
- 纯渲染引擎，非完整应用
- 需要配合 UI 框架使用
- 无后端功能（无转换、无 PACS 代理）

---

## 四、改进建议（按优先级排序）

### 高优先级（核心竞争力提升）

#### 4.1 引入 Cornerstone3D 作为渲染引擎

**当前问题**: Canvas 2D 渲染无法提供 3D 体渲染能力，性能受限。

**建议方案**:
- 替换自建的 `image_builder.py` + Canvas 渲染为 Cornerstone3D
- 实现 MPR（多平面重建）、MIP（最大密度投影）、VR（体渲染）
- 利用 WebGL GPU 加速提升大体积数据渲染性能

**预期收益**: 获得与 OHIF 同级别的渲染能力，支持放疗计划的 3D 可视化。

**工作量**: 中等 — 需要替换前端渲染逻辑，后端保留切片数据生成。

#### 4.2 支持 DICOMweb 协议（WADO-RS / QIDO-RS / STOW-RS）

**当前问题**: 用户必须手动上传 DICOM 文件，无法直接连接 PACS。

**建议方案**:
- 实现 WADO-RS（Web Access to DICOM Objects）用于检索影像
- 实现 QIDO-RS（Query based on ID for DICOM Objects）用于查询
- 实现 STOW-RS（Store over the Web）用于存储
- 可使用现有 DICOMweb 客户端库（如 `dicom-web-client`）

**预期收益**: 允许直接从 PACS 服务器加载影像，大幅扩展使用场景。

**工作量**: 中等 — 新增 DICOMweb 数据源，复用现有 session 管理。

#### 4.3 添加 DICOM Segmentation 支持

**当前问题**: 放疗中 SEG 文件越来越常见（自动分割结果），当前不支持。

**建议方案**:
- 集成 Cornerstone3D 的 SEG 解码器
- 在前端实现分割掩码的叠加显示
- 支持多标签分割（不同 ROI 不同颜色）

**预期收益**: 覆盖放疗工作流中的自动分割结果查看需求。

**工作量**: 低 — Cornerstone3D 已有现成解码库。

### 中优先级（功能完善）

#### 4.4 插件化架构

**当前问题**: 所有功能硬编码在路由和服务中，社区难以贡献扩展。

**建议方案**:
- 参考 OHIF 的 Mode/Extension 模式
- 将 RT 查看、剂量查看、NIfTI 转换等作为可选插件
- 定义标准的插件接口（数据加载、渲染、工具栏）

**预期收益**: 社区可贡献扩展，降低核心复杂度，提升可维护性。

**工作量**: 高 — 需要重构前端和后端的模块组织。

#### 4.5 测量和标注工具

**当前问题**: 只有 RT 结构叠加，没有交互式测量功能。

**建议方案**:
- 长度测量（两点距离）
- 角度测量（三点角度）
- ROI 统计（平均值、最大值、标准差）
- 箭头标注和文字标注
- 测量结果导出

**预期收益**: 满足放疗科医生的日常测量需求。

**工作量**: 中等 — 需要前端交互层 + 后端统计计算。

#### 4.6 4D 动态序列支持

**当前问题**: 4D-CT 用于呼吸运动管理，当前不支持时间维度。

**建议方案**:
- 数据层支持多时间点体积数据
- 前端添加时间轴滑块和播放控件
- 支持关键帧跳转

**预期收益**: 覆盖 4D-CT 放疗模拟的需求。

**工作量**: 中等 — 数据层 + UI 时间轴组件。

### 低优先级（锦上添花）

#### 4.7 DICOM Anonymization 增强

**当前建议**: 当前 anonymize 功能已有，可增加更细粒度的控制（选择性保留字段），参考 DICOM 标准的 Profile 机制。

**工作量**: 低

#### 4.8 前端纯客户端模式

**当前建议**: 参考 DWV，支持部分功能（查看、测量）在纯前端运行，仅在需要 NIfTI 转换等重计算时才连接后端。可考虑将部分 Python 解析逻辑编译为 WebAssembly。

**工作量**: 高

#### 4.9 OpenID Connect / OAuth 2.0 认证

**当前建议**: 医疗场景通常需要身份认证和审计。可集成 Keycloak 或其他 IdP 实现 SSO 登录。

**工作量**: 中等

#### 4.10 国际化扩展

**当前建议**: 当前支持中英双语，可扩展到日韩法德等语言。i18n 框架已就绪，主要工作是翻译内容。

**工作量**: 低

---

## 五、项目独特优势

在分析竞品后，本项目也有以下差异化优势：

1. **NIfTI 转换 + SSE 实时进度** — 竞品大多不提供 DICOM→NIfTI 的转换功能，更没有 SSE 流式进度推送
2. **RT 支持开箱即用** — OHIF 的 RT 支持需要安装扩展，本项目原生支持 RT Structure + RT Dose
3. **轻量部署** — Docker 一键部署，比 Weasis 的 Java 安装简单得多
4. **客户端预览** — 上传前用 dicom-parser 做客户端预览，竞品中很少有这个功能
5. **二进制切片传输** — 比 JSON 传输小 60%，性能优化亮点
6. **Vue 3 技术栈** — 轻量、响应式，适合中小型团队快速二次开发

---

## 六、总结

| 维度 | 当前水平 | 目标水平 | 关键改进 |
|------|---------|---------|---------|
| 渲染能力 | Canvas 2D | WebGL 3D | 引入 Cornerstone3D |
| 数据接入 | 手动上传 | PACS 直连 | DICOMweb 协议 |
| SOP Class | CT/MR + RT | 全覆盖 | +SEG +SR |
| 架构扩展性 | 单体 | 插件化 | Extension 机制 |
| 交互工具 | 无 | 测量标注 | 交互式工具集 |
| 部署复杂度 | 中等 | 低 | 纯前端模式 |

**最高 ROI 改进路径**: 引入 Cornerstone3D 替换自建渲染层 → 添加 DICOMweb 支持 → 集成 SEG 解码器。这三步将使项目从"上传查看工具"升级为"可连接 PACS 的专业影像工作站"。
