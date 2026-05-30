<p align="right">
  <a href="./README.md">English</a> | <b>中文</b>
</p>

# MedVista

基于 Web 的放射治疗医学影像查看与处理平台。支持 DICOM、NIfTI、NRRD、MHA 格式，具备 WebGL 3D 渲染、结构/剂量叠加、RT 计划分析和 PACS 连接功能。

**在线体验：** https://medical.1661688.xyz

![Vue 3](https://img.shields.io/badge/Vue-3-42b883?logo=vue.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178c6?logo=typescript)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-06b6d4?logo=tailwindcss)
![Cornerstone3D](https://img.shields.io/badge/Cornerstone3D-4.22-ff6b35)

## 功能特性

### WebGL 3D 查看器（Cornerstone3D）
- **GPU 加速渲染** — 基于 Cornerstone3D 的 WebGL 渲染，实时 MPR（轴位、矢状位、冠状位）
- **同步十字线** — 使用 Cornerstone3D `CrosshairsTool` 跨平面定位
- **窗宽/窗位预设** — CT、肺、骨、软组织、脑、硬膜下等预设，支持交互调整
- **体素检查** — 光标位置实时 HU/值读数
- **DICOM 标签查看器** — 可搜索、可过滤的标签查看器
- **影像控制** — 旋转、翻转、缩放/平移速度、方向标签

### 测量与标注工具
- **长度工具** — mm 距离测量
- **角度工具** — 角度测量（度）
- **ROI 统计** — 矩形/椭圆 ROI，显示平均值、标准差、最小值、最大值 HU
- **探针工具** — 点值检查
- **箭头标注** — 图像文字标注
- **测量导出** — CSV 导出所有测量数据
- **持久化标注** — 按检查保存/加载标注

### DICOM 分割（SEG）支持
- **SEG 对象解析** — 解析 DICOM SEG 对象并提取二进制掩模
- **分割叠加** — 在体数据上显示分割掩模叠加
- **逐段控制** — 每个分割区域独立的颜色、可见性和透明度
- **分割面板** — 侧边栏分割管理面板

### 结构与剂量叠加
- **RT 结构叠加** — 彩色轮廓渲染，可调节透明度和线宽
- **ROI 居中** — 一键导航至任意结构中心
- **TG-263 类型推断** — 自动结构类型分类（靶区、危及器官、外轮廓等）
- **剂量叠加** — 色彩映射剂量分布可视化
- **剂量合并** — 将多个剂量分布合并为单一剂量体

### 4D 动态序列支持
- **时间序列数据** — 支持 4D-CT、心脏 MRI、动态增强序列
- **时间滑块** — 播放/暂停、帧率控制、逐步导航
- **自动检测** — 从 DICOM TemporalPositionIdentifier 检测时间位置

### RT 计划
- **计划查看器** — 射束摘要，包含能量、机架角度和权重
- **分次显示** — 分次数、每次剂量、总剂量

### DICOMweb / PACS 连接
- **QIDO-RS 查询** — 搜索远程 PACS 上的研究/序列/实例
- **WADO-RS 检索** — 从 PACS 获取 DICOM 对象
- **STOW-RS 存储** — 推送 DICOM 对象到 PACS
- **多服务器** — 同时管理多个 PACS 连接
- **PACS 浏览器** — 树形浏览研究/序列/实例

### DICOM 匿名化
- **配置文件** — 预定义配置：研究、临床试验、完全去标识化
- **自定义规则** — 逐标签匿名化规则（移除、哈希、替换、偏移）
- **日期偏移** — 可配置的日期偏移，用于时间匿名化
- **预览模式** — 应用前预览匿名化变更
- **审计日志** — 追踪所有匿名化操作

### 后处理
- **HU-RED 转换** — CT Hounsfield 单位转相对电子密度，450+ 标定表
- **TG-263 自动重命名** — 批量将结构重命名为 TG-263 标准命名
- **剂量合并** — 将多个剂量分布合并为单一剂量体
- **NRRD 导出** — 将 CT (HU) 和 RED 体导出为 NRRD 文件

### 转换器与序列分析
- **DICOM 转 NIfTI** — 支持 SSE 实时进度的格式转换
- **智能序列分析** — 自动分类为 ADC、DWI、DCE、MG、US 类型
- **DCE 期相检测** — 按时间位置或采集时间分组
- **智能序列选择** — 基于文件数、几何匹配自动选择最佳序列

### 纯客户端模式
- **离线 DICOM 查看器** — 使用 `dicom-parser` 在浏览器端解析和查看 DICOM
- **无需后端** — 无需运行后端服务器
- **拖拽上传** — 直接拖拽 DICOM 文件到查看器

### PWA 与离线支持
- **渐进式 Web 应用** — 通过 manifest.json 支持桌面和移动端安装
- **Service Worker 缓存** — 使用 SHA-256 请求体哈希作为缓存键自动缓存切片响应
- **离线重复访问** — 之前查看的切片可从缓存离线获取

### WebWorker 渲染与解析
- **OffscreenCanvas 渲染** — 在专用 WebWorker 中完成影像合成和窗宽窗位调整（不阻塞 UI）
- **后台 DICOM 解析** — 大量上传时批量元数据提取卸载到 WebWorker
- **主线程降级** — WebWorker 不可用时优雅降级到主线程

### HTTP/2 多路复用
- **HTTP/2 协议** — 多路复用连接，切片/体积请求无队头阻塞
- **自动降级** — h2 不可用时自动降级到 HTTP/1.1

### 认证（OIDC）
- **OpenID Connect** — 支持任何 OIDC 提供商（Keycloak、Auth0 等）
- **JWT 令牌** — 安全的基于令牌的会话管理
- **路由保护** — 除登录/回调外所有路由的认证守卫
- **可配置** — 通过环境变量启用/禁用

### 可扩展性与内存管理
- **客户端元数据预览** — 使用 `dicom-parser` 在浏览器端解析 DICOM 元数据
- **二进制切片传输** — 原始字节传输（比 JSON 小约 60%）
- **磁盘像素存储** — 上传后立即保存像素数据为 `.npy` 文件
- **资源限制** — 单会话：10,000 文件，最大 2 GB
- **会话清理** — 15 分钟 TTL + 2 分钟清理周期
- **流式体积传输** — 大体积以 4MB 分块流式传输，避免超时
- **切片预加载** — 后台预加载相邻切片，实现平滑导航
- **虚拟滚动** — DICOM 标签表仅渲染可见行，支持大量标签
- **LRU 缓存** — 体积、结构、剂量使用有界内存缓存

### 多格式支持
| 格式 | 扩展名 | 读取库 |
|------|--------|--------|
| DICOM | `.dcm` | pydicom |
| NIfTI | `.nii`, `.nii.gz` | nibabel |
| NRRD | `.nrrd`, `.nhdr` | pynrrd |
| MHA/MHD | `.mha`, `.mhd` | SimpleITK |

### 其他
- **双语界面** — 英文和简体中文 (zh-CN)
- **深色模式** — 完整深色/浅色主题支持
- **响应式布局** — 桌面和移动端友好界面
- **实时活动日志** — 跟踪所有处理操作
- **可配置设置** — 窗位预设、叠加默认值、交互速度
- **安全加固** — SSRF 防护、路径遍历防护、速率限制、安全 CORS

## 架构

```
MedVista/
├── backend/                      # FastAPI + Python
│   ├── app/
│   │   ├── main.py               # 应用入口、CORS、路由
│   │   ├── routers/
│   │   │   ├── dicom.py          # DICOM 上传、切片、结构、剂量、计划、volume-binary
│   │   │   ├── auth.py           # OIDC 登录、JWT、令牌刷新
│   │   │   ├── dicomweb.py       # PACS 连接（QIDO/WADO/STOW-RS）
│   │   │   ├── seg.py            # DICOM 分割对象
│   │   │   ├── four_d.py         # 4D 时间序列数据
│   │   │   ├── annotations.py    # 测量/标注持久化
│   │   │   ├── anonymization.py  # DICOM 匿名化配置
│   │   │   ├── converter.py      # DICOM 转 NIfTI（SSE 进度）
│   │   │   ├── analysis.py       # 序列分析
│   │   │   ├── export.py         # NRRD 体导出
│   │   │   ├── postprocessing.py # HU-RED、剂量合并、TG-263
│   │   │   ├── medical_formats.py# NIfTI/NRRD/MHA 上传
│   │   │   ├── config.py         # TG-263 配置、窗位预设
│   │   │   └── logging.py        # 活动日志
│   │   ├── services/
│   │   │   ├── dicom_service.py          # 会话管理、磁盘存储
│   │   │   ├── auth_service.py           # JWT、OIDC 发现、JWKS
│   │   │   ├── dicomweb_service.py       # DICOMweb HTTP 客户端
│   │   │   ├── seg_service.py            # SEG 对象解析
│   │   │   ├── four_d_service.py         # 4D 体构建
│   │   │   ├── anonymization_service.py  # 匿名化引擎
│   │   │   ├── image_builder.py          # 体构建与切片
│   │   │   ├── rt_struct_builder.py      # RT 结构轮廓
│   │   │   ├── rt_dose_builder.py        # RT 剂量网格
│   │   │   ├── dicom_converter_service.py# DICOM 转 NIfTI
│   │   │   ├── sequence_analysis_service.py
│   │   │   ├── nifti_service.py          # NIfTI/NRRD/MHA 加载器
│   │   │   └── log_service.py
│   │   └── middleware/
│   │       └── auth.py           # FastAPI 认证依赖
│   ├── config_files/             # TG-263 命名、器官匹配、预设
│   ├── requirements.txt
│   └── run.py
├── frontend/                     # Vue 3 + TypeScript + Cornerstone3D
│   ├── src/
│   │   ├── views/                # 15 个页面视图
│   │   ├── components/
│   │   │   ├── layout/           # AppLayout、AppSidebar、AppHeader、AuthGuard
│   │   │   ├── viewer/           # Cornerstone3DViewer、MeasurementToolbar/Panel、
│   │   │   │                     # SegmentationPanel、TimeSlider、ViewerHeader、
│   │   │   │                     # ViewerSidebar、ImageSliceViewer（Canvas2D）
│   │   │   ├── pacs/             # PacsConnectionDialog、PacsBrowser
│   │   │   └── common/           # DataTable、StatusBadge 等
│   │   ├── composables/
│   │   │   ├── useCornerstone3D  # Cornerstone3D 引擎生命周期
│   │   │   ├── useTools          # 测量工具管理
│   │   │   ├── useSegmentation   # SEG 叠加状态
│   │   │   ├── useDicomweb       # PACS 连接状态
│   │   │   ├── useFourD          # 4D 时间序列状态
│   │   │   ├── useAnonymization  # 匿名化状态
│   │   │   ├── useAuth           # OIDC 登录/令牌管理
│   │   │   └── useClientMode     # 后端可用性检测
│   │   ├── utils/
│   │   │   ├── cornerstoneVolumeLoader.ts  # 自定义体积加载器
│   │   │   ├── clientDicomLoader.ts        # 客户端 DICOM 解析器
│   │   │   ├── dicomClientParser.ts        # 客户端 DICOM 解析（WebWorker）
│   │   │   └── webglDetector.ts            # GPU 能力检测
│   │   ├── workers/
│   │   │   ├── render.worker.ts            # OffscreenCanvas 渲染
│   │   │   └── dicom-parse.worker.ts       # 后台 DICOM 解析
│   │   ├── stores/               # Pinia 状态管理
│   │   ├── i18n/                 # 英文 + 中文翻译
│   │   ├── router/               # Vue Router + 认证守卫
│   │   └── types/                # TypeScript 接口
│   ├── tailwind.config.js
│   └── vite.config.ts
└── docs/                         # 竞品分析
```

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+ / pnpm

### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务（多 worker）
python run.py
```

后端运行在 `http://localhost:8000`

### 前端

```bash
cd frontend

# 安装依赖
pnpm install

# 开发模式
pnpm dev

# 生产构建
pnpm build
node server.cjs
```

前端运行在 `http://localhost:3000`（生产代理）

### 认证（可选）

```bash
# 设置以下环境变量以启用 OIDC 认证
export OIDC_ISSUER=https://your-oidc-provider.com
export JWT_SECRET=your-strong-random-secret
export CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### API 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/dicom/upload` | 上传 DICOM 文件 |
| POST | `/api/dicom/volume-binary` | 获取原始 3D 体积（用于 Cornerstone3D） |
| POST | `/api/dicom/slice` | 获取影像切片（JSON） |
| POST | `/api/dicom/slice-binary` | 获取影像切片（二进制，小约 60%） |
| DELETE | `/api/dicom/session/{session_id}` | 显式会话清理 |
| GET | `/api/dicom/patients/{session}` | 获取患者列表 |
| GET | `/api/dicom/structs/{session}/{patient}` | 获取 RT 结构列表 |
| GET | `/api/dicom/dose/{session}/{patient}/{uid}/{slice}` | 获取剂量切片 |
| GET | `/api/dicom/plans/{session}/{patient}` | 获取 RT 计划 |
| POST | `/api/seg/mask` | 获取 SEG 二进制掩模 |
| POST | `/api/seg/volume` | 获取 SEG 体积数据 |
| GET | `/api/4d/info` | 获取 4D 序列信息 |
| POST | `/api/4d/volume` | 获取指定时间点的 4D 体积 |
| POST | `/api/dicomweb/connect` | 连接 PACS 服务器 |
| GET | `/api/dicomweb/studies` | 搜索 PACS 上的研究 |
| GET | `/api/dicomweb/studies/{uid}/retrieve` | 从 PACS 检索研究 |
| POST | `/api/annotations/save` | 保存标注 |
| GET | `/api/annotations/{session}` | 加载标注 |
| POST | `/api/anonymization/apply` | 应用匿名化 |
| GET | `/api/anonymization/profiles` | 获取匿名化配置列表 |
| POST | `/api/converter/scan` | 扫描患者序列 |
| POST | `/api/converter/convert-stream` | DICOM 转 NIfTI（SSE） |
| POST | `/api/analysis/analyze` | 分析 DICOM 序列 |
| POST | `/api/postprocessing/convert-hu` | HU 转 RED |
| POST | `/api/postprocessing/sum-doses` | 剂量合并 |
| GET | `/api/export/nrrd/{session}/{patient}/{series}` | 导出 NRRD 体 |
| POST | `/api/auth/login` | 登录（OIDC 或本地） |
| GET | `/api/auth/me` | 获取当前用户 |
| POST | `/api/auth/refresh` | 刷新 JWT 令牌 |
| POST | `/api/auth/logout` | 登出 |
| GET | `/api/auth/config` | 认证配置（启用/禁用） |

## 配置

配置文件位于 `backend/config_files/`：

| 文件 | 用途 |
|------|------|
| `tg263_names.json` | TG-263 结构名称映射 |
| `organ_matching.json` | 器官名称匹配规则 |
| `window_presets.json` | 窗宽/窗位预设 |
| `ct_HU_map_vals.json` | HU 标定值 |
| `ct_RED_map_vals.json` | RED 标定值 |
| `disease_sites.json` | 治疗部位定义 |

## 技术栈

- **前端**：Vue 3、TypeScript、Pinia、Vue Router、Vue I18n、Tailwind CSS、Vite、Cornerstone3D
- **后端**：Python、FastAPI、Uvicorn、pydicom、nibabel、SimpleITK、pynrrd、NumPy、Pillow、httpx
- **设计**：玻璃拟态 UI + 网格渐变背景

## 许可证

MIT
