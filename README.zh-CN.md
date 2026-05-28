<p align="right">
  <a href="./README.md">English</a> | <b>中文</b>
</p>

# MedicalDataHandler Web

基于 Web 的放射治疗医学影像查看与处理平台。支持 DICOM、NIfTI、NRRD、MHA 格式，具备多平面重建、结构/剂量叠加和 RT 计划分析功能。

**在线体验：** https://medical.1661688.xyz

![Vue 3](https://img.shields.io/badge/Vue-3-42b883?logo=vue.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178c6?logo=typescript)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-06b6d4?logo=tailwindcss)

## 功能特性

### 影像查看器
- **多平面重建 (MPR)** — 轴位、矢状位、冠状位同步导航
- **同步十字线** — 跨平面定位，精确导航
- **窗宽/窗位预设** — CT、肺、骨、软组织、脑、硬膜下等预设
- **体素检查** — 光标位置实时 HU/值读数
- **DICOM 标签查看器** — 可搜索、可过滤的标签查看器
- **影像控制** — 旋转、翻转、缩放/平移速度、方向标签

### 结构与剂量叠加
- **RT 结构叠加** — 彩色轮廓渲染，可调节透明度和线宽
- **ROI 居中** — 一键导航至任意结构中心
- **TG-263 类型推断** — 自动结构类型分类（靶区、危及器官、外轮廓等）
- **剂量叠加** — 色彩映射剂量分布可视化
- **剂量合并** — 将多个剂量分布合并为单一剂量体

### RT 计划
- **计划查看器** — 射束摘要，包含能量、机架角度和权重
- **分次显示** — 分次数、每次剂量、总剂量

### 后处理
- **HU-RED 转换** — CT Hounsfield 单位转相对电子密度，450+ 标定表
- **TG-263 自动重命名** — 批量将结构重命名为 TG-263 标准命名
- **剂量合并** — 将多个剂量分布合并为单一剂量体
- **NRRD 导出** — 将 CT (HU) 和 RED 体导出为 NRRD 文件，用于 AI/ML 管线

### 转换器与序列分析
- **DICOM 转 NIfTI** — 将 DICOM 序列转换为 NIfTI 格式，支持 SSE 实时进度
- **智能序列分析** — 基于高级 DICOM 标签（DiffusionBValue、TemporalPositionIdentifier、ContrastBolusAgent、ImageType 等）自动分类为 ADC、DWI、DCE、MG、US 类型
- **DCE 期相检测** — 按时间位置或采集时间对动态增强序列分组
- **DWI b 值分析** — 从切片几何推断 b 值数量（单/双 b 值）
- **智能序列选择** — 基于文件数、几何匹配和临床规则自动选择各类型最佳序列
- **DICOM 匿名化** — 从 DICOM 文件中去除患者 PHI（个人身份信息）

### 可扩展性与内存管理
- **磁盘像素存储** — 上传后立即保存像素数据为 `.npy` 文件，内存中仅保留元数据。支持单会话数万个 DICOM 文件。
- **上传验证** — 限制：单会话 50,000 文件，总上传大小 20 GB
- **后台会话清理** — 过期会话（30 分钟 TTL）每 5 分钟自动清理，包括磁盘文件
- **优化转换** — 预分配体数组 + 按需加载像素，降低 NIfTI 转换峰值内存

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

## 架构

```
MedicalDataHandler-Web/
├── backend/                  # FastAPI + Python
│   ├── app/
│   │   ├── main.py          # 应用入口、CORS、路由
│   │   ├── routers/         # API 端点
│   │   │   ├── dicom.py     # DICOM 上传、切片、结构、剂量、计划、ROI 边界
│   │   │   ├── converter.py # DICOM 转 NIfTI（扫描、流式转换、匿名化、下载）
│   │   │   ├── analysis.py  # 序列分析（ADC/DWI/DCE/MG/US 分类）
│   │   │   ├── export.py    # NRRD 体导出
│   │   │   ├── postprocessing.py  # HU-RED、剂量合并、TG-263 重命名
│   │   │   ├── medical_formats.py # NIfTI/NRRD/MHA 上传
│   │   │   ├── config.py    # TG-263 配置、窗位预设
│   │   │   └── logging.py   # 活动日志
│   │   ├── services/        # 业务逻辑
│   │   │   ├── dicom_service.py    # DICOM 会话管理、磁盘像素存储、后台清理
│   │   │   ├── dicom_converter_service.py # DICOM 转 NIfTI（按需像素加载、预分配体）
│   │   │   ├── sequence_analysis_service.py # 智能序列分类与选择
│   │   │   ├── image_builder.py    # 体构建与切片提取
│   │   │   ├── rt_struct_builder.py # RT 结构轮廓处理
│   │   │   ├── rt_dose_builder.py  # RT 剂量网格处理
│   │   │   ├── nifti_service.py    # NIfTI/NRRD/MHA 加载器
│   │   │   └── log_service.py      # 活动日志
│   │   └── utils/
│   ├── config_files/        # TG-263 命名、器官匹配、窗位预设
│   ├── requirements.txt
│   └── run.py               # Uvicorn 启动器
├── frontend/                 # Vue 3 + TypeScript
│   ├── src/
│   │   ├── views/           # 9 个页面视图
│   │   ├── components/      # 可复用组件
│   │   │   ├── layout/      # AppLayout、AppSidebar、AppHeader
│   │   │   ├── viewer/      # ImageSliceViewer（基于 Canvas）
│   │   │   └── common/      # DataTable、StatusBadge、SequenceCard 等
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── i18n/            # 英文 + 中文翻译
│   │   ├── router/          # Vue Router 懒加载
│   │   └── types/           # TypeScript 接口
│   ├── server.cjs           # 生产代理（提供构建产物 + 代理 API）
│   ├── tailwind.config.js
│   └── vite.config.ts
└── test-data/               # 测试用 DICOM 样本文件
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

### API 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/dicom/upload` | 上传 DICOM 文件 |
| POST | `/api/upload/medical` | 上传 NIfTI/NRRD/MHA 文件 |
| GET | `/api/dicom/patients/{session}` | 获取患者列表 |
| POST | `/api/dicom/slice` | 获取影像切片 |
| GET | `/api/dicom/structs/{session}/{patient}` | 获取 RT 结构列表 |
| GET | `/api/dicom/struct-mask/{session}/{patient}/{key}/{slice}` | 获取结构掩模 |
| GET | `/api/dicom/roi-bounds/{session}/{patient}/{key}` | 获取 ROI 边界框 |
| GET | `/api/dicom/dose/{session}/{patient}/{uid}/{slice}` | 获取剂量切片 |
| GET | `/api/dicom/plans/{session}/{patient}` | 获取 RT 计划 |
| POST | `/api/converter/scan` | 扫描患者序列 |
| POST | `/api/converter/convert-stream` | DICOM 转 NIfTI（SSE 进度） |
| POST | `/api/converter/anonymize` | 匿名化 DICOM 文件 |
| GET | `/api/converter/download/{session}/{filename}` | 下载转换文件 |
| POST | `/api/analysis/analyze` | 分析与分类 DICOM 序列 |
| POST | `/api/postprocessing/convert-hu` | HU 转 RED |
| POST | `/api/postprocessing/sum-doses` | 剂量合并 |
| POST | `/api/postprocessing/auto-rename-structs` | TG-263 批量重命名 |
| GET | `/api/export/nrrd/{session}/{patient}/{series}` | 导出 NRRD 体 |

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

- **前端**：Vue 3、TypeScript、Pinia、Vue Router、Vue I18n、Tailwind CSS、Vite
- **后端**：Python、FastAPI、Uvicorn、pydicom、nibabel、SimpleITK、pynrrd、NumPy、Pillow
- **设计**：玻璃拟态 UI + 网格渐变背景

## 许可证

MIT
