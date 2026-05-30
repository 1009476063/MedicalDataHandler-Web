# MedVista 项目逻辑深度分析

> 分析日期: 2026-05-30
> 分析范围: 全项目前后端处理逻辑、GPU 检测机制、运行路径、功能矩阵、改进建议

---

## 一、项目架构总览

```
MedVista/
├── backend/                    # Python FastAPI 服务器
│   ├── app/
│   │   ├── main.py             # 应用入口, 中间件, 路由注册
│   │   ├── routers/            # 15 个路由模块 (DICOM, 导出, 配置, 认证等)
│   │   ├── services/           # 核心业务逻辑 (图像构建, RT结构, 剂量, 分割等)
│   │   ├── models/             # Pydantic 数据模型
│   │   └── utils/              # 工具 (LRU 缓存, 速率限制)
│   ├── uploads/                # 临时 DICOM 存储 (会话级)
│   └── configs/                # 运行时配置文件
│
└── frontend/                   # Vue 3 + TypeScript + Pinia
    ├── src/
    │   ├── views/              # 页面视图
    │   ├── components/         # UI 组件
    │   ├── composables/        # 组合式函数 (工具, 分割, 4D, 客户端模式)
    │   ├── stores/             # Pinia 状态管理 (app, session, patient, viewer)
    │   ├── api/                # Axios API 客户端层
    │   ├── utils/              # 工具 (WebGL 检测, 体积加载器, 客户端 DICOM 加载器)
    │   └── types/              # TypeScript 类型定义
    └── vite.config.ts          # 构建配置 (Cornerstone3D 代码分割)
```

**技术栈**: Python 3.11+ / FastAPI / pydicom / NumPy | Vue 3 / TypeScript / Pinia / Cornerstone3D / Tailwind CSS

**核心功能**: 医学 DICOM 影像浏览器 — 支持 3D 体积渲染、RT 结构/剂量叠加、分割叠加、4D 时间序列、测量标注、NRRD 导出、DICOM 匿名化、多格式转换

---

## 二、前端处理逻辑

### 2.1 应用启动流程

```
main.ts
  → createApp(App)
  → 注册 Pinia, vue-i18n, vue-router, AppLayout
  → App.vue 路由出口
    → /viewer → ViewerView.vue (核心查看器页面)
```

### 2.2 ViewerView 启动决策树

```
ViewerView.vue onMounted()
  │
  ├── detectWebGL()                    # webglDetector.ts
  │   ├── 创建离屏 canvas
  │   ├── 尝试 getContext('webgl2')
  │   ├── 无 WebGL2 → 尝试 getContext('webgl')
  │   ├── 获取 renderer/vendor/maxTextureSize
  │   └── 释放上下文 (WEBGL_lose_context)
  │
  ├── WebGL 不可用 → useCanvasFallback = true
  │   └── 跳过 Cornerstone3D 初始化
  │
  ├── WebGL 可用 → 初始化 Cornerstone3D
  │   ├── registerMdhVolumeLoader()     # 注册自定义 mdh:// 体积加载器
  │   ├── isClientMode → registerClientLoaders()  # 注册客户端 DICOM 加载器
  │   ├── 创建 RenderingEngine
  │   ├── 设置 3 个视口 (轴位/矢状/冠状)
  │   └── 监听 WebGL 上下文丢失/恢复事件
  │
  └── Cornerstone3D 构造函数异常 → 回退 Canvas2D
```

### 2.3 数据加载流程

```
用户选择 Series (watch selectedSeriesUid)
  │
  └── loadSeriesData()                 # 并行加载 (Promise.all)
      ├── getSeriesInfo()              # 体积形状/间距/范围
      ├── getStructs()                 # RT 结构列表 (非客户端模式)
      ├── getDoseInfo()                # 剂量信息列表 (非客户端模式)
      ├── loadDicomTags()              # DICOM 标签详情
      │
      └── 渲染路径选择
          │
          ├── WebGL 模式 → loadVolumeIntoViewports()
          │   ├── 从后端 POST /api/dicom/volume-binary 获取二进制体积
          │   ├── cornerstoneVolumeLoader.ts 解析 response headers
          │   │   (x-volume-shape, x-volume-spacing, x-volume-origin, x-volume-dtype)
          │   ├── 转换 ArrayBuffer → TypedArray (Float32/Int16/Uint8...)
          │   ├── 构造 IImageVolume 对象
          │   └── RenderingEngine.setViewportVolumes() → 3 个视口同时渲染
          │
          └── Canvas2D 模式 → loadSlicesForCanvas()  # 并行加载 3 个方向
              ├── POST /api/dicom/slice-binary (axial, sagittal, coronal)
              ├── 获取 uint8 像素数据 + 窗位信息
              └── ImageSliceViewer canvas 渲染
```

### 2.4 渲染管线对比

| 特性 | Cornerstone3D (WebGL) | Canvas2D 回退 |
|------|----------------------|---------------|
| 渲染引擎 | GPU 加速 WebGL2 | CPU 软件渲染 |
| 体积加载 | 完整 3D 体积一次性加载 | 逐切片 2D 获取 |
| 窗位调整 | GPU shader 实时计算 | 重新请求后端切片 |
| 测量工具 | Length/Angle/ROI/Elliptical/Probe/Arrow/Crosshairs (7种) | Length/Probe (2种) |
| 交叉线 | Cornerstone3D Crosshairs 工具 | 手动 canvas 绘制 |
| 结构叠加 | Cornerstone3D overlay API | Canvas 半透明层叠加 |
| 性能 | 60fps GPU 加速 | CPU 逐像素处理 |
| 内存 | GPU 纹理内存 | JS 堆内存 |

### 2.5 客户端模式 (Client Mode)

```
后端不可用 (checkBackend() 3s 超时)
  │
  ├── uploadFiles() → 后端上传失败
  │   └── 自动回退到 loadClientFilesAction()
  │
  ├── loadClientFiles(files)
  │   ├── 逐文件读取 ArrayBuffer
  │   ├── parseDicomMetadata(buffer)    # dicom-parser 浏览器内解析
  │   │   ├── 提取 ~30 个关键 DICOM tag
  │   │   ├── patientId, patientName, modality, UIDs
  │   │   ├── pixelSpacing, rows, columns, bitsAllocated
  │   │   └── windowCenter/Width, rescaleSlope/Intercept
  │   ├── storeDicomBuffer(buffer)      # 存入内存 Map<number, ArrayBuffer>
  │   └── 返回 ClientPatient[] 层级结构
  │
  ├── getSeriesImageIds(seriesUid)
  │   ├── 按 instanceNumber 排序
  │   └── 返回 mdh-client-dcm:{index} imageId 数组
  │
  └── Cornerstone3D 使用 imageId 加载每张图像
      ├── clientDicomLoader.ts 加载器
      ├── dicom-parser 解析像素数据
      ├── rescaleSlope/Intercept → Float32Array
      ├── MONOCHROME1 反转处理
      └── 构造 IImage 对象返回给 Cornerstone3D
```

**限制**: 客户端模式仅支持单张切片加载，不支持完整 3D 体积渲染 (内存限制)。

---

## 三、后端处理逻辑

### 3.1 请求处理流程

```
HTTP Request
  │
  ├── CORS 中间件 (检查 origin)
  ├── slowapi 速率限制 (全局 200/min)
  ├── 路由匹配 (15 个 router)
  │
  └── 路由处理
      ├── 参数校验 (Pydantic model)
      ├── 会话验证 (session_id 格式 + 存在性)
      ├── 业务逻辑 (service 调用)
      │   └── CPU 密集操作 → asyncio.to_thread() 包装
      └── 返回 ApiResponse { success, data, error }
```

### 3.2 DICOM 上传流程

```
POST /api/dicom/upload (multipart/form-data)
  │
  ├── 速率限制: 10 次/分钟
  ├── 并发控制: Semaphore(2) 最多 2 个并行上传
  │
  ├── 资源检查
  │   ├── 文件数量 ≤ 10,000
  │   ├── 总大小 ≤ 2GB
  │   └── 磁盘剩余 ≥ 500MB (上传大小 × 2)
  │
  ├── 创建会话
  │   ├── session_id = uuid4().hex (32 字符)
  │   ├── 创建 uploads/{session_id}/pixels/ 目录
  │   └── 初始化 session dict
  │
  └── 逐文件处理
      ├── pydicom.dcmread(force=True) 解析
      ├── 提取 DICOM 标签 (~30 个关键 tag + all_tags 截断 500 字符)
      ├── 判断模态类型
      │   ├── CT/MR/PT/NM/US/XA/OT → 提取像素数据
      │   │   ├── 应用 RescaleSlope/Intercept
      │   │   ├── np.save() → pixels/{file_id}.npy
      │   │   └── 存储 metadata (不保留像素到内存)
      │   └── RTSTRUCT/RTDOSE/RTPLAN/SEG → 存储原始字节
      └── 构建患者→研究→系列→文件 层级结构
```

### 3.3 图像构建流程 (ImageBuilder)

```
get_slice(session_id, patient_id, series_uid, orientation, slice_index, wc, ww)
  │
  ├── _build_volume()                    # 构建或从缓存获取 3D 体积
  │   ├── 按 patient_id + modality + series_uid 过滤文件
  │   ├── 加载 .npy 文件到内存
  │   ├── 按 slice_location 排序 (fallback: instance_number)
  │   ├── np.stack() → 3D ndarray (slices, rows, cols)
  │   ├── 计算 spacing (层间距 + 像素间距)
  │   └── LRU 缓存 (maxsize=5)
  │
  ├── 切片提取
  │   ├── axial (轴位): volume[slice_index, :, :]
  │   ├── sagittal (矢状): volume[:, :, slice_index]
  │   └── coronal (冠状): volume[:, slice_index, :]
  │
  ├── 窗位处理
  │   ├── 提供 wc/ww → 直接裁剪+缩放
  │   └── 未提供 → 1st-99th 百分位自动窗位
  │
  ├── 返回格式
  │   ├── get_slice(): .tolist() → JSON (体积大 3-5x)
  │   ├── get_slice_binary(): .tobytes() → 二进制 (~60% 更小)
  │   └── get_volume_binary(): 完整体积 → 二进制 + HTTP headers
  │
  └── 切片缓存 (LRU maxsize=10)
```

### 3.4 RT 结构处理流程

```
GET /api/dicom/structs/{session_id}/{patient_id}
  │
  └── RTStructBuilder
      ├── 从 session raw_data 加载 RTSTRUCT 原始字节
      ├── pydicom 解析 → ROI Contour Sequence
      ├── 提取每个 ROI: number, name, type
      └── 返回 StructInfo[] 列表

GET /api/dicom/struct-mask/{session_id}/{patient_id}/{struct_key}/{slice_index}
  │
  └── RTStructBuilder.get_struct_mask()
      ├── 加载体积数据获取 spacing/origin
      ├── 获取 ROI Contour Sequence
      ├── 将 3D 坐标转换为切片像素坐标
      ├── 逐 contour 绘制多边形填充
      ├── 创建 (rows, cols) uint8 mask
      └── 返回二进制 mask 数据
```

### 3.5 RT 剂量处理流程

```
GET /api/dicom/dose/{session_id}/{patient_id}/{dose_uid}/{slice_index}
  │
  └── RTDoseBuilder
      ├── 解析 RTDOSE 文件
      ├── 提取 Dose Grid (3D 剂量矩阵)
      ├── 获取 GridFrameOffsetVector (层间距)
      ├── 提取指定切片的剂量数据
      ├── 转换为 (rows, cols) float 数组
      └── 返回剂量值 + 坐标信息
```

### 3.6 GPU 检测流程 (后端)

```
GET /api/system/gpu-info
  │
  └── system.py
      ├── 检查 CUDA 是否可用
      │   └── torch.cuda.is_available() (如安装 PyTorch)
      ├── 调用 nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv
      ├── 解析 GPU 信息
      ├── 5 分钟 TTL 缓存 (避免频繁调用 nvidia-smi)
      └── 返回 { gpu_available, gpu_name, ... }
```

**注意**: 后端 GPU 信息仅用于状态显示，不影响实际图像处理。所有图像处理均在 CPU 上完成 (NumPy)。

---

## 四、GPU 检测逻辑

### 4.1 前端 WebGL 检测 (决定渲染路径)

```typescript
// webglDetector.ts
detectWebGL(): WebGLCapability {
  1. 创建离屏 <canvas> 元素
  2. canvas.getContext('webgl2')     // 优先 WebGL2
  3. 无 WebGL2 → canvas.getContext('webgl')  // 回退 WebGL1
  4. 通过 WEBGL_debug_renderer_info 获取:
     - renderer: GPU 型号 (如 "NVIDIA GeForce RTX 3090")
     - vendor: GPU 厂商 (如 "NVIDIA Corporation")
  5. 获取 MAX_TEXTURE_SIZE, MAX_VIEWPORT_DIMS
  6. 通过 WEBGL_lose_context 释放上下文
  7. 返回 WebGLCapability 对象
}
```

**决策逻辑**:
- `webgl2 = true` → 使用 Cornerstone3D (完整 3D 渲染)
- `webgl1 = true` (无 WebGL2) → 尝试 Cornerstone3D (部分功能可能受限)
- `webgl2 = false, webgl1 = false` → Canvas2D 回退

### 4.2 前端 GPU 状态显示

```
ViewerHeader.vue 状态徽章:
  ├── gpuInfo.gpu_available = true → 绿色 "GPU: {gpu_name}" 徽章
  ├── canvasMode = true → 橙色 "Canvas2D" 徽章
  ├── clientMode = true → 琥珀色 "Client Mode" 徽章
  └── canvasMode + 有推荐 → 信息图标 + 浏览器推荐悬浮卡
```

### 4.3 后端 GPU 检测 (仅供参考)

```
GET /api/system/gpu-info
  ├── 返回: { gpu_available: bool, gpu_name: str, ... }
  ├── 缓存: 5 分钟 TTL
  └── 用途: 仅用于前端显示 GPU 状态，不影响渲染路径选择
```

**关键点**: 后端 GPU 检测和前端 WebGL 检测是**独立的两个系统**:
- 前端 WebGL 检测 → 决定**渲染路径** (Cornerstone3D vs Canvas2D)
- 后端 GPU 检测 → 仅**显示信息** (服务器有无 GPU)

---

## 五、运行路径分析

### 5.1 有 GPU + WebGL 完整路径 (最佳体验)

```
条件: 浏览器支持 WebGL2 + 后端运行中
  │
  ├── 渲染: Cornerstone3D WebGL2 GPU 加速
  ├── 数据: 后端 volume-binary 传输完整 3D 体积
  ├── 测量: 7 种工具 (Length, Angle, RectangleROI, EllipticalROI, Probe, ArrowAnnotate, Crosshairs)
  ├── 叠加: RT 结构/剂量/分割 全功能
  ├── 4D: 时间序列播放
  ├── 导出: NRRD 批量导出
  └── 性能: 60fps 流畅交互
```

### 5.2 无 GPU / 无 WebGL 回退路径

```
条件: 浏览器不支持 WebGL 或上下文创建失败
  │
  ├── 渲染: Canvas2D CPU 软件渲染
  ├── 数据: 后端 slice-binary 逐切片传输
  ├── 测量: 2 种工具 (Length, Probe)
  ├── 叠加: RT 结构/剂量仍可用 (canvas 半透明层)
  ├── 4D: 时间序列播放
  ├── 导出: NRRD 批量导出
  ├── 限制: 无 Angle/ROI/Elliptical/Arrow/Crosshairs
  ├── 限制: 窗位调整需重新请求后端
  └── 提示: Header 显示浏览器推荐 (Chrome/Edge/Firefox)
```

### 5.3 Client Mode (无后端) 路径

```
条件: 后端不可达 (checkBackend() 3s 超时) + 用户上传文件
  │
  ├── 渲染: Cornerstone3D (有 WebGL) 或 Canvas2D (无 WebGL)
  ├── 解析: 浏览器内 dicom-parser 完全前端解析
  ├── 数据: 内存中 ArrayBuffer 存储
  ├── 测量: WebGL=7种, Canvas2D=2种
  ├── 叠加: 无 (RT/剂量需要后端)
  ├── 4D: 无 (需要后端)
  ├── 导出: 无 (需要后端)
  ├── 限制: 内存受限 (大文件集可能 OOM)
  └── 限制: 无 RT 结构/剂量/分割功能
```

### 5.4 功能矩阵

| 功能 | 有 GPU + 后端 | 无 GPU + 后端 | Client Mode |
|------|:---:|:---:|:---:|
| DICOM 上传 | ✅ | ✅ | ✅ (前端解析) |
| 患者/系列浏览 | ✅ | ✅ | ✅ |
| 3D 体积渲染 | ✅ WebGL GPU | ✅ Canvas2D CPU | ⚠️ 有限 |
| 切片浏览 (轴/矢/冠) | ✅ | ✅ | ✅ |
| 窗位/窗宽调整 | ✅ 实时 GPU | ⚠️ 重新请求 | ✅ |
| 测量 (长度) | ✅ | ✅ | ✅ |
| 测量 (角度) | ✅ | ❌ | ✅ (WebGL) |
| 测量 (ROI/椭圆) | ✅ | ❌ | ✅ (WebGL) |
| 测量 (探针) | ✅ | ✅ | ✅ |
| 测量 (箭头标注) | ✅ | ❌ | ✅ (WebGL) |
| 交叉线同步 | ✅ | ✅ | ✅ |
| RT 结构叠加 | ✅ | ✅ | ❌ |
| RT 剂量叠加 | ✅ | ✅ | ❌ |
| DICOM SEG 分割 | ✅ | ✅ | ❌ |
| 4D 时间序列 | ✅ | ✅ | ❌ |
| NRRD 导出 | ✅ | ✅ | ❌ |
| DICOM 匿名化 | ✅ | ✅ | ❌ |
| 格式转换 | ✅ | ✅ | ❌ |
| DICOMweb 协议 | ✅ | ✅ | ❌ |
| 浏览器推荐提示 | — | ✅ | — |

---

## 六、会话管理

```
Session 生命周期:
  │
  ├── 创建: POST /api/dicom/upload → uuid4().hex (32字符)
  ├── 存储: 内存 dict (非 Redis/数据库)
  ├── TTL: 15 分钟 (SESSION_TTL = 900)
  ├── 清理: 后台 asyncio 任务每 2 分钟扫描
  ├── 限制: 最大 10,000 文件 / 2GB 总大小
  └── 删除: DELETE /api/dicom/session/{id} 或 TTL 过期
```

**安全措施**:
- session_id 格式验证: `r'^[0-9a-f]{32}$'`
- 路径遍历防护: 解析后验证 upload 目录前缀
- 文件系统清理: 会话删除时清理 uploads/ 目录

---

## 七、API 响应标准化

所有端点统一返回格式:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

错误时:
```json
{
  "success": false,
  "data": null,
  "error": "Error message"
}
```

---

## 八、改进建议

### 8.1 架构改进

| 优先级 | 建议 | 影响 |
|:---:|------|------|
| P0 | **会话存储 → Redis**: 当前内存 dict 重启丢失，多 worker 不共享。迁移到 Redis 支持持久化和水平扩展 | 可靠性 |
| P0 | **认证中间件**: 大部分端点无鉴权，仅 login 端点有速率限制。应添加 JWT 中间件保护敏感端点 | 安全性 |
| P1 | **SessionData TypedDict 不匹配**: `dicom_service.py` 的 TypedDict 定义与实际 dict 结构不一致，从未被用于类型检查 | 可维护性 |
| P1 | **rename_struct 非功能**: `struct_key` (ROI 编号) 与 `file_id` (UUID) 永远不匹配，方法实际上不可用 | 功能缺陷 |
| P1 | **重复 ImageBuilder 实例**: 每次导入都创建新实例，应使用单例模式 | 内存 |
| P2 | **SSE 进程超时**: 转换任务的 SSE 端点可能无限挂起，需要超时机制 | 稳定性 |

### 8.2 性能改进

| 优先级 | 建议 | 影响 |
|:---:|------|------|
| P0 | **GPU 加速图像处理**: 当前窗位/切片处理全在 CPU (NumPy)，可用 CUDA 加速或 OpenCL | 渲染速度 |
| P1 | **流式体积传输**: 大体积 (>100MB) 应支持分块流式传输，避免单次请求超时 | 大文件 |
| P1 | **切片缓存预热**: 首次加载时预取相邻切片，减少浏览延迟 | 用户体验 |
| P2 | **HTTP/2 多路复用**: 确保部署时启用 HTTP/2，减少并发请求开销 | 传输效率 |
| P2 | **WebWorker 解析**: 客户端模式的 DICOM 解析移入 WebWorker，避免阻塞主线程 | 响应性 |

### 8.3 安全改进

| 优先级 | 建议 | 影响 |
|:---:|------|------|
| P0 | **SSRF 防护**: `connect_pacs` 端点接受任意 URL，应拦截私有 IP | 安全性 |
| P0 | **CORS 白名单**: 生产环境应从环境变量读取允许的 origins | 安全性 |
| P1 | **上传文件类型校验**: 应验证文件魔数 (DICOM preamble `DICM`)，防止伪装文件 | 安全性 |
| P1 | **请求体大小限制**: 全局最大请求体限制，防止内存耗尽 | 稳定性 |
| P2 | **API 密钥认证**: 为 API 端点添加 API 密钥认证，支持外部集成 | 安全性 |

### 8.4 前端改进

| 优先级 | 建议 | 影响 |
|:---:|------|------|
| P1 | **WebWorker 渲染**: Canvas2D 渲染循环移入 OffscreenCanvas + Worker | 流畅度 |
| P1 | **Service Worker 缓存**: 缓存已加载的切片数据，减少重复请求 | 离线能力 |
| P2 | **PWA 支持**: 添加 manifest.json 和 Service Worker，支持离线查看已缓存数据 | 可用性 |
| P2 | **虚拟滚动**: 大量 DICOM 标签列表使用虚拟滚动 | 性能 |

### 8.5 测试改进

| 优先级 | 建议 | 影响 |
|:---:|------|------|
| P0 | **API 集成测试**: 为 15 个路由模块添加 pytest 集成测试 | 质量 |
| P1 | **E2E 测试**: Playwright 覆盖上传→浏览→测量→导出核心流程 | 质量 |
| P1 | **性能基准测试**: 建立 DICOM 加载/渲染性能基准 | 性能 |

### 8.6 可观测性改进

| 优先级 | 建议 | 影响 |
|:---:|------|------|
| P1 | **结构化日志**: 将 print/log 替换为 structlog 或 loguru，支持 JSON 格式 | 运维 |
| P1 | **请求追踪**: 添加 request_id 中间件，支持跨服务追踪 | 调试 |
| P2 | **Prometheus 指标**: 暴露请求数/延迟/错误率指标 | 监控 |

---

## 九、关键发现汇总

### 已修复的问题 (本项目周期内)

1. ✅ JWT 空密钥 → 随机生成 fallback
2. ✅ 无界 dict 缓存 → LRU bounded cache
3. ✅ 速率限制 → slowapi 全局 + 端点级限制
4. ✅ CORS 硬化 → 环境变量配置
5. ✅ Session ID 熵 → uuid4 hex (32 字符)
6. ✅ 路径遍历防护 → 会话目录验证
7. ✅ API 响应标准化 → ApiResponse 模型
8. ✅ 前端 API 客户端层 → Axios 封装
9. ✅ Store 拆分 → session/patient/viewer 模块
10. ✅ 组件拆分 → ViewerHeader/ViewerSidebar
11. ✅ 后端 to_thread → 阻塞端点异步化
12. ✅ 全局异常处理器
13. ✅ Cornerstone3D 代码分割 → 手动 chunk
14. ✅ 数据加载并行化 → Promise.all
15. ✅ GPU 浏览器推荐 → ViewerHeader 悬浮提示

### 待修复的已知问题

1. ❌ `SessionData TypedDict` 与实际结构不匹配
2. ❌ `rename_struct` 方法因 key 类型不匹配而不可用
3. ❌ `rt_struct_builder` 的 `slice_index` 参数未被使用
4. ❌ `system.py` 中 `cuda_version` 字段名不准确 (应为 `cuda_version` → `driver_version`)
5. ❌ 部分端点返回格式不一致 (未包裹 ApiResponse)

---

## 十、数据流全景图

```
用户浏览器                    后端服务器                  存储
    │                           │                        │
    │  POST /upload (DICOM)     │                        │
    │ ─────────────────────────>│                        │
    │                           │── pydicom 解析 ──────>│ uploads/{sid}/pixels/*.npy
    │                           │── 构建层级结构 ──────>│ 内存 dict
    │  { session_id }           │                        │
    │ <─────────────────────────│                        │
    │                           │                        │
    │  GET /volume-binary       │                        │
    │ ─────────────────────────>│                        │
    │                           │── 加载 .npy ─────────>│ 读取磁盘
    │                           │── np.stack → 3D        │
    │  [binary + headers]       │                        │
    │ <─────────────────────────│                        │
    │                           │                        │
    │  Cornerstone3D 渲染       │                        │
    │  (WebGL2 GPU 加速)        │                        │
    │                           │                        │
    │  GET /struct-mask         │                        │
    │ ─────────────────────────>│                        │
    │                           │── RTStructBuilder      │
    │                           │── 坐标转换 + 绘制      │
    │  [binary mask]            │                        │
    │ <─────────────────────────│                        │
    │                           │                        │
    │  Canvas 叠加渲染          │                        │
    │  (半透明结构层)           │                        │
    │                           │                        │
    │  DELETE /session          │                        │
    │ ─────────────────────────>│                        │
    │                           │── 清理 uploads/ ──────>│ 删除文件
    │                           │── 清理内存 dict        │
    │  { success: true }        │                        │
    │ <─────────────────────────│                        │
```

---

*本文档基于源码静态分析生成，覆盖 MedVista 项目全部前后端模块。*
