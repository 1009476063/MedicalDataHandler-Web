# MedVista 项目架构深度分析

> 生成时间：2026-05-30

---

## 一、项目概览

MedVista 是一个医学影像处理平台，支持 DICOM/NIfTI/NRRD/MHA 等格式的上传、查看、测量、导出和后处理。架构分为前后端分离的两个独立系统：

| 维度 | 技术栈 | 核心职责 |
|------|--------|---------|
| **后端** | FastAPI + Python (numpy/scipy/pydicom/SimpleITK) | DICOM 解析、体积构建、窗位处理、RT 结构/剂量、转换、匿名化 |
| **前端** | Vue 3 + Pinia + vue-router + Cornerstone3D | 图像渲染、交互工具、UI 控制、DICOMweb 连接 |

---

## 二、后端处理逻辑

### 2.1 请求处理架构

```
客户端请求 → FastAPI (uvicorn) → Router → Service → numpy/scipy/pydicom 处理 → JSON/Binary 响应
```

关键设计模式：

- **异步事件循环**：FastAPI 使用 `asyncio` 事件循环处理 HTTP 请求
- **CPU 密集型任务线程化**：所有体积构建、窗位处理、结构掩码计算等用 `asyncio.to_thread()` 包装，避免阻塞事件循环
- **内存会话管理**：DICOM 数据以嵌套 dict 形式驻留在 `dicom_service.sessions` 中，像素数据存磁盘 `.npy` 文件
- **单例模式**：`dicom_service`、`image_builder`、`struct_builder`、`dose_builder` 均为模块级单例

### 2.2 数据流完整路径

```
用户上传 DICOM 文件
  ↓
POST /api/dicom/upload (multipart/form-data)
  ↓
dicom_service.process_upload_bytes()
  ├── 验证：文件数 ≤10000，总大小 ≤2GB，磁盘剩余 ≥500MB
  ├── 并发控制：信号量限制最多 2 个上传并发
  ├── 解析：pydicom 解析每个文件，提取 26 个 DICOM 标签
  ├── 像素提取：RescaleSlope/Intercept 变换 → 存为 .npy 文件
  └── 返回：{session_id, patients, file_count}
  ↓
前端选择 series → 请求切片
  ↓
POST /api/dicom/slice
  ↓
image_builder.get_slice()
  ├── 加载：从 .npy 文件读取像素 → np.stack 组装 3D 体积（带缓存）
  ├── 切面提取：轴位/矢状/冠状方向
  ├── 窗位/窗宽：(val - lower) / (upper - lower) → uint8 归一化
  └── 返回：number[][] (JSON) 或 binary (uint8)
  ↓
前端渲染
  ├── WebGL 模式：Cornerstone3D 通过 volume-binary 加载 3D 体积
  └── Canvas2D 模式：ImageSliceViewer 逐像素渲染
```

### 2.3 后端服务清单

| 服务 | 行数 | 职责 | GPU 潜力 |
|------|------|------|---------|
| `dicom_service.py` | 467 | 会话管理、DICOM 解析、标签提取 | 低 |
| `image_builder.py` | 186 | 体积构建、切片提取、窗位处理 | **高** — np.stack + np.clip 并行计算 |
| `rt_struct_builder.py` | 249 | RTSTRUCT 轮廓解析、掩码渲染 | 中 |
| `rt_dose_builder.py` | 156 | RTDOSE 网格提取、色图插值 | **高** — 剂量重采样并行 |
| `seg_service.py` | 310 | DICOM SEG 解析、掩码提取 | 中 |
| `nifti_service.py` | 358 | NIfTI/NRRD/MHA 加载 | 低 — I/O 瓶颈 |
| `dicom_converter_service.py` | 640 | DICOM→NIfTI 并行转换 + 匿名化 | 中 |
| `sequence_analysis_service.py` | 544 | MR 序列分类 (DWI/ADC/DCE) | 低 |
| `anonymization_service.py` | 424 | 匿名化引擎 (3 套 profile) | 低 |
| `four_d_service.py` | 149 | 4D 时序分组、体积装配 | 低 |
| `auth_service.py` | 137 | OIDC/JWT 认证 | 无 |

### 2.4 会话生命周期

```
上传创建 session → TTL 900s (15分钟) → 清理任务每 120s 扫描 → 过期删除
                                                      ↓
                                              删除磁盘 .npy 文件
                                              删除 uploads/{session_id}/ 目录
```

### 2.5 并发控制

| 资源 | 信号量 | 说明 |
|------|--------|------|
| 文件上传 | 2 | 最多 2 个并发上传 |
| 格式转换 | 2 | 最多 2 个并发转换 |
| CPU 核心 | min(cpu_count, 8) | ThreadPoolExecutor 线程数 |
| SSE 连接 | queue.Queue 桥接 | 线程→异步 SSE 事件流 |

---

## 三、前端处理逻辑

### 3.1 渲染引擎架构

```
应用启动
  ↓
detectWebGL() 探测 Canvas 能力
  ├── WebGL2 可用 → Cornerstone3D 渲染引擎 (GPU 加速)
  ├── WebGL1 可用 → Cornerstone3D (降级)
  └── 均不可用 → ImageSliceViewer (Canvas2D 纯 CPU 渲染)
```

### 3.2 WebGL 模式 (完整功能)

```
Cornerstone3D v4.22
  ↓
初始化 RenderingEngine('cs3d-engine')
  ├── 创建 3 个 ORTHOGRAPHIC 视口 (axial/sagittal/coronal)
  ├── 注册 mdh://volume 自定义 volume loader
  ├── 创建测量工具组 (Length/Angle/ROI/Probe/Arrow/Crosshairs)
  └── 绑定注释事件监听器
  ↓
加载体积数据
  ├── POST /api/dicom/volume-binary → 二进制 ArrayBuffer
  ├── ArrayBuffer → TypedArray (Float64/Int16/Uint16/...)
  ├── 构造 IImageVolume 对象 (dimensions/spacing/origin/direction)
  └── 设置到 3 个视口
  ↓
交互
  ├── 鼠标拖拽：切片滚动
  ├── Shift+拖拽：窗位/窗宽调整
  ├── Ctrl+拖拽：平移
  ├── Ctrl+滚轮：缩放
  └── 测量工具：实时标注 + 统计面板
```

### 3.3 Canvas2D 模式 (降级功能)

```
ImageSliceViewer.vue
  ↓
三个独立的 ImageSliceViewer 组件 (axial/sagittal/coronal)
  ↓
每个组件独立获取切片
  POST /api/dicom/slice → number[][] (JSON)
  ↓
Canvas2D 逐像素渲染
  ├── 1. 创建 ImageData (cols × rows × 4)
  ├── 2. 归一化：(val - lower) / (upper - lower) → 0~255 灰度
  ├── 3. 绘制到离屏 Canvas
  ├── 4. 缩放绘制到主 Canvas
  ├── 5. 叠加绘制 overlay (fill/contour 模式)
  └── 6. 绘制标注 (Length 线段/Probe 十字)
  ↓
交互
  ├── 左键拖拽：切片滚动
  ├── Shift+拖拽：窗位/窗宽
  ├── Ctrl+拖拽/中键：平移
  ├── Ctrl+滚轮：缩放
  └── 测量工具：Length + Probe (无 Angle/ROI)
```

### 3.4 状态管理

整个前端使用**单一 Pinia Store** (`useAppStore`) 作为数据中心：

```
useAppStore (429 行)
  ├── sessionId          — 后端会话标识
  ├── patients[]         — 患者列表
  ├── selectedPatientId  — 当前选中患者
  ├── selectedSeriesUid  — 当前选中 series
  ├── isClientMode       — 是否纯浏览器模式
  ├── uploading/uploadProgress — 上传状态
  │
  ├── API 方法 (20+)
  │   ├── uploadFiles()         — 上传文件
  │   ├── getSlice()            — 获取 2D 切片 (JSON)
  │   ├── getVolumeBinary()     — 获取 3D 体积 (二进制)
  │   ├── getSeriesInfo()       — 获取体积元数据
  │   ├── getStructs()          — RT 结构列表
  │   ├── getStructMask()       — RT 结构掩码
  │   ├── getDoseInfo/Slice()   — RT 剂量数据
  │   ├── getSegFiles/Mask()    — SEG 分割数据
  │   ├── get4DInfo/Volume()    — 4D 时序数据
  │   ├── getFileMetadata()     — DICOM 标签
  │   ├── cleanupSession()      — 清理会话
  │   └── exportNrrd()          — NRRD 导出
  │
  └── Client 模式方法
      ├── loadClientFiles()     — 浏览器端解析 DICOM
      └── getClientPatients()   — 浏览器端患者分组
```

### 3.5 Composables 体系

| Composable | 行数 | 职责 |
|-----------|------|------|
| `useTheme.ts` | 29 | 暗色/亮色主题切换 |
| `useCornerstone3D.ts` | 127 | Cornerstone3D 引擎封装 |
| `useTools.ts` | 163 | 测量工具组管理 |
| `useDicomweb.ts` | 118 | PACS 连接 (QIDO/WADO/STOW) |
| `useAnonymization.ts` | 117 | 匿名化工作流 |
| `useSegmentation.ts` | 96 | SEG 叠加管理 |
| `useFourD.ts` | 131 | 4D 时序播放 |
| `useAuth.ts` | 163 | OIDC 认证 |
| `useClientMode.ts` | 183 | 纯浏览器模式 |
| `useCanvasTools.ts` | 56 | Canvas2D 测量工具 |

---

## 四、GPU 检测逻辑

项目有**两个完全独立的 GPU 检测维度**，彼此无关联：

### 4.1 客户端 WebGL 检测

**文件**: `frontend/src/utils/webglDetector.ts` (40 行)

```
创建临时 Canvas
  ↓
尝试 getContext('webgl2')
  ├── 成功 → 标记 webgl2=true
  └── 失败 → 尝试 getContext('webgl1')
              ├── 成功 → 标记 webgl1=true
              └── 失败 → webgl2=false, webgl1=false
  ↓
读取 WEBGL_debug_renderer_info 扩展
  ├── renderer: GPU 渲染器名称
  ├── vendor: GPU 厂商
  ├── maxTextureSize: 最大纹理尺寸
  └── maxViewportDims: 最大视口尺寸
  ↓
丢失上下文 (释放 GPU 资源)
  ↓
返回 { webgl2, webgl1, renderer, vendor, maxTextureSize, maxViewportDims }
```

**消费位置**: `ViewerView.vue` 的 `onMounted` 中调用 `detectWebGL()`

- WebGL2/WebGL1 可用 → `useCanvasFallback = false` → Cornerstone3D 渲染
- 均不可用 → `useCanvasFallback = true` → ImageSliceViewer 渲染

### 4.2 服务端 GPU 检测

**文件**: `backend/app/routers/system.py` (39 行)

```
GET /api/system/gpu-info
  ↓
执行 nvidia-smi 子进程
  ├── 成功 → 解析 GPU 名称、显存、CUDA 版本
  └── 失败 → { gpu_available: false }
  ↓
返回 { gpu_available, gpu_name, cuda_version, gpu_memory_mb }
```

**消费位置**: 前端 `ViewerView.vue` 中 fetch `/api/system/gpu-info`，显示 GPU 状态徽章

**关键问题**: 后端检测到 GPU 后**不会利用 GPU 进行任何计算**。`nvidia-smi` 结果仅作为状态信息展示，不驱动任何后端处理路径的分支。

### 4.3 检测维度对比

| 维度 | 检测对象 | 检测方式 | 影响范围 | 是否被消费 |
|------|---------|---------|---------|-----------|
| **WebGL** | 浏览器 GPU 能力 | `canvas.getContext('webgl')` | 前端渲染引擎选择 | **是** — 驱动 WebGL/Canvas2D 分支 |
| **nvidia-smi** | 服务器 GPU 硬件 | 子进程调用 | 无 | **仅展示** — 不影响后端处理路径 |

---

## 五、无 GPU vs 有 GPU 运行路径

### 5.1 WebGL 可用时 (浏览器有 GPU)

```
前端：Cornerstone3D WebGL2 硬件加速渲染
  ├── 三个 ORTHOGRAPHIC 视口 (axial/sagittal/coronal)
  ├── 体积数据流式加载 (mdh://volume → volume-binary)
  ├── GPU 硬件加速窗位调整 (voiRange)
  ├── GPU 纹理变换 (缩放/平移/旋转)
  └── 同步十字线 (CrosshairsTool) 三视口联动

后端：CPU 处理 (无变化)
  ├── image_builder: np.stack 体积组装 → tobytes() 返回
  └── 所有计算仍在 CPU
```

**功能完整性**: 100%

### 5.2 WebGL 不可用时 (浏览器无 GPU / Canvas2D 降级)

```
前端：Canvas2D 纯 CPU 渲染
  ├── 三个 ImageSliceViewer 组件
  ├── 每个切片独立 POST 请求获取 (非体积加载)
  ├── 逐像素 CPU 归一化渲染到 Canvas
  ├── 缩放/平移通过 Canvas transform 矩阵实现
  └── 无同步十字线 (仅屏幕空间虚线)

后端：CPU 处理 (无变化)
  ├── image_builder: np.stack 体积组装 → .tolist() 返回 JSON
  └── 窗位处理在 CPU 逐切片执行
```

**功能完整性**: ~40%

### 5.3 功能差异矩阵

| 功能 | WebGL 模式 | Canvas2D 模式 | 差异 |
|------|-----------|-------------|------|
| **三平面视图** | 完整 MPR | 三个独立 2D 视图 | 无联动 |
| **切片滚动** | 流式体积加载 | 逐张请求后端 | 响应慢 |
| **窗位调整** | GPU 硬件加速 | CPU 逐像素归一化 | 性能差 |
| **缩放/平移** | GPU 纹理变换 | Canvas transform | 基本等价 |
| **同步十字线** | CrosshairsTool 三视口联动 | 仅屏幕空间虚线，无联动 | **丧失** |
| **Length 测量** | Cornerstone3D LengthTool (mm) | Canvas2D 原生 Length (mm) | 功能等价 |
| **Angle 测量** | Cornerstone3D AngleTool (°) | **不可用** | **丧失** |
| **RectangleROI** | Cornerstone3D (面积/HU/标准差) | **不可用** | **丧失** |
| **EllipticalROI** | Cornerstone3D (面积/HU/标准差) | **不可用** | **丧失** |
| **Probe** | Cornerstone3D ProbeTool (HU) | Canvas2D 原生 Probe (HU) | 功能等价 |
| **ArrowAnnotate** | Cornerstone3D 箭头标注 | **不可用** | **丧失** |
| **RT 结构叠加** | Cornerstone3D overlay | Canvas2D fill/contour | 等价 |
| **RT 剂量叠加** | Cornerstone3D overlay | **未实现** | **丧失** |
| **SEG 叠加** | Cornerstone3D overlay | **未实现** | **丧失** |
| **4D 播放** | Cornerstone3D 时序切换 | **未实现** | **丧失** |
| **标注持久化** | 事件驱动标注系统 | 仅内存，不持久 | **降级** |
| **截图** | canvas.toDataURL | canvas.toDataURL | 等价 |
| **DICOM 标签** | 侧边栏 | 同左 | 等价 |
| **方向标签** | Cornerstone3D overlay | ImageSliceViewer 内置 | 等价 |
| **MeasurementToolbar** | 完整 6 工具 | 仅 Length + Probe | **降级** |

---

## 六、改进方案

### 6.1 架构级改进

#### P0: 后端 GPU 加速路径

**问题**: 后端检测到 GPU 后不利用 GPU 进行任何计算，`nvidia-smi` 检测是死代码。

**方案**: 为计算密集型服务添加 GPU 加速路径：

```python
# image_builder.py — 体积构建加速
try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

def _build_volume(self, ...):
    if GPU_AVAILABLE:
        # CuPy 并行体积组装
        slices_gpu = cp.array([cp.asarray(s) for s in sorted_slices])
        volume = cp.stack(slices_gpu, axis=0)
    else:
        # NumPy CPU 路径 (现有逻辑)
        volume = np.stack(sorted_slices, axis=0)
```

候选 GPU 加速服务（按优先级）：

| 服务 | 操作 | GPU 加速方案 | 预期加速 |
|------|------|------------|---------|
| `image_builder.py` | `np.stack` 体积组装 | CuPy `cp.stack` | 5-10x |
| `rt_dose_builder.py` | 剂量网格重采样 | CuPy 插值 | 3-5x |
| `seg_service.py` | `scipy.ndimage.zoom` | CuPy zoom | 2-4x |
| `rt_struct_builder.py` | PIL polygon 掩码 | OpenCV GPU | 2-3x |

#### P1: 前后端 GPU 状态联动

**问题**: 前后端 GPU 检测完全独立，后端 GPU 信息不驱动任何前端行为。

**方案**: 将后端 GPU 信息纳入前端决策链：

```typescript
// ViewerView.vue — 启动时同时检测
onMounted(async () => {
  // 客户端 WebGL 检测
  webglCap.value = detectWebGL()
  useCanvasFallback.value = !webglCap.value.webgl2 && !webglCap.value.webgl1

  // 服务端 GPU 检测
  const resp = await fetch('/api/system/gpu-info')
  const gpu = await resp.json()

  // 新增：如果服务端有 GPU 且客户端无 WebGL，
  // 可以提示用户使用支持 WebGL 的浏览器以获得 GPU 加速
  if (!webglCap.value.webgl1 && gpu.gpu_available) {
    showGpuHint.value = true
  }
})
```

#### P2: Canvas2D 模式体积加载优化

**问题**: Canvas2D 模式每个切片独立请求后端，切换切片有明显延迟。

**方案**: 预加载当前切片前后 N 张切片：

```typescript
async function preloadSlices(orientation: string, currentIndex: number, range = 5) {
  const promises = []
  for (let i = currentIndex - range; i <= currentIndex + range; i++) {
    if (i < 0 || i > canvasMaxSlice.value[orientation]) continue
    if (i === currentIndex) continue
    promises.push(
      appStore.getSlice(seriesUid, orientation, i, wc, ww)
        .then(data => { sliceCache[orientation][i] = data?.data })
    )
  }
  await Promise.allSettled(promises)
}
```

### 6.2 功能级改进

#### Canvas2D 模式功能补齐

| 优先级 | 功能 | 实现方案 | 复杂度 |
|--------|------|---------|--------|
| P0 | RT 剂量叠加 | 后端 `get_dose_slice()` 已可用，前端 ImageSliceViewer 添加 dose overlay 渲染 | 低 |
| P1 | SEG 叠加 | 后端 `get_seg_mask()` 已可用，前端添加 SEG overlay 渲染 | 低 |
| P1 | 4D 播放 | 后端 `get_4d_volume()` 已可用，前端添加 TimeSlider 联动 | 中 |
| P2 | Angle 测量 | Canvas2D 三点角度计算（已知两点向量夹角） | 低 |
| P2 | ROI 测量 | Canvas2D 矩形/椭圆区域像素统计 (mean HU, std dev) | 中 |
| P3 | 同步十字线 | 跨组件事件总线，3 个 ImageSliceViewer 联动 crosshair 坐标 | 中 |
| P3 | 标注持久化 | Canvas 标注存入后端 annotations API | 低 |

### 6.3 后端改进

#### P0: 会话持久化

**问题**: 所有数据在内存中，重启丢失；单 worker 限制（多 worker 会破坏会话共享）。

**方案**: 分层存储：

```python
# 方案 A: Redis 会话存储
# 方案 B: SQLite + 文件系统 (更轻量)
class SessionStore:
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)
        self._init_tables()  # sessions, patients, series, files

    def save_session(self, session_id, data):
        # 元数据 → SQLite
        # 像素文件 → uploads/{session_id}/pixels/ (保持现有方案)
        pass

    def load_session(self, session_id):
        # 从 SQLite 恢复元数据
        # 像素按需从磁盘加载
        pass
```

#### P1: API 响应格式统一

**问题**: 部分端点返回裸数据，部分返回 `{success, data, error}` 信封。

**方案**: 统一响应格式：

```python
from pydantic import BaseModel
from typing import Any, Optional

class ApiResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None

class PaginatedResponse(ApiResponse):
    meta: dict = {}  # {total, page, limit}
```

#### P2: 缓存策略

**问题**: `image_builder._cache` 使用简单的 dict 缓存，无 LRU 淘汰，大数据体积可能导致内存溢出。

**方案**: 使用 `functools.lru_cache` 或自定义 LRU：

```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, maxsize=5):
        self._cache = OrderedDict()
        self._maxsize = maxsize

    def get(self, key):
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def put(self, key, value):
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)
```

#### P3: 结构化日志

**问题**: `log_service.py` 使用内存 deque，日志随进程死亡丢失。

**方案**: 集成 `structlog` 或 `loguru`：

```python
import structlog

logger = structlog.get_logger()

# 替代现有的 log_service.log()
logger.info("upload_started", session_id=session_id, file_count=len(files))
```

### 6.4 前端改进

#### P0: Store 拆分

**问题**: `useAppStore` 429 行，承担了所有状态管理（上传、患者、series、测量、4D、SEG...），职责过重。

**方案**: 按功能域拆分：

```typescript
// stores/upload.ts — 上传逻辑
// stores/patient.ts — 患者/series 选择
// stores/viewer.ts — 查看器状态 (窗位、overlay、测量)
// stores/session.ts — 会话管理
```

#### P1: 组件拆分

**问题**: `ViewerView.vue` 超过 1000 行，包含侧边栏控制、渲染逻辑、工具管理。

**方案**: 提取子组件：

```
ViewerView.vue (路由入口)
  ├── ViewerSidebar.vue (侧边栏控制面板)
  ├── ViewerToolbar.vue (顶部工具栏)
  └── ViewerMain.vue (三平面渲染区)
```

#### P2: 网络请求层

**问题**: 所有 API 调用分散在 store 的各个方法中，缺乏统一的错误处理和重试逻辑。

**方案**: 创建 API 客户端层：

```typescript
// api/client.ts
const api = axios.create({ baseURL: '/api' })

api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (error.response?.status === 429) {
      toast.warning('服务器繁忙，请稍后重试')
    }
    if (error.response?.status === 401) {
      auth.logout()
    }
    return Promise.reject(error)
  }
)
```

### 6.5 安全改进

| 优先级 | 问题 | 位置 | 方案 |
|--------|------|------|------|
| P0 | CORS 允许 localhost:5173/3000 | `main.py` | 生产环境使用环境变量严格配置 |
| P1 | JWT_SECRET 可选 | `auth_service.py` | 强制要求，未设置时拒绝启动 |
| P1 | 会话 ID 仅 8 位 hex | `dicom_service.py` | 增加到 16 位或使用 UUID |
| P2 | 无请求速率限制 | 全局 | 添加 `slowapi` 或 nginx 限流 |
| P2 | 无 CORS 凭据保护 | `main.py` | 添加 `allow_credentials=True` 限制 |

---

## 七、性能优化建议

### 7.1 后端性能

| 优化点 | 当前实现 | 优化方案 | 预期收益 |
|--------|---------|---------|---------|
| 体积构建缓存 | dict 无淘汰 | LRU 缓存 (maxsize=5) | 减少内存峰值 |
| 切片返回格式 | `.tolist()` (JSON) | Binary 返回 (arraybuffer) | 传输体积减小 3-5x |
| 并发上传 | 信号量=2 | 提升到 CPU 核心数 | 上传吞吐提升 |
| 窗位处理 | 每次请求重新计算 | 缓存处理后的 uint8 切片 | 响应时间减小 50%+ |
| 像素存储 | `.npy` 文件 | 压缩存储 (np.savez_compressed) | 磁盘占用减小 40%+ |

### 7.2 前端性能

| 优化点 | 当前实现 | 优化方案 | 预期收益 |
|--------|---------|---------|---------|
| 切片预加载 | 无 | 预加载前后 5 张切片 | 滚动响应延迟消除 |
| Canvas2D 渲染 | 逐像素循环 | OffscreenCanvas + Web Worker | 主线程阻塞减少 |
| Cornerstone3D 初始化 | 同步创建 | 懒初始化 + 动态 import | 首屏加载加速 |
| 测量面板 | 每次注释变化全量刷新 | 增量更新 | 减少不必要的渲染 |
| 大体积传输 | 全量 JSON | 流式 binary (ReadableStream) | 内存峰值降低 |

---

## 八、涉及文件索引

### 核心文件

| 文件 | 行数 | 职责 |
|------|------|------|
| `backend/app/main.py` | 56 | FastAPI 入口、路由注册 |
| `backend/app/services/dicom_service.py` | 467 | 会话管理、DICOM 解析 |
| `backend/app/services/image_builder.py` | 186 | 体积构建、切片提取 |
| `backend/app/routers/dicom.py` | 226 | 核心 DICOM API |
| `frontend/src/views/ViewerView.vue` | ~1100 | 主查看器 (双模式) |
| `frontend/src/stores/app.ts` | 429 | Pinia 中央状态 |
| `frontend/src/components/viewer/ImageSliceViewer.vue` | 635 | Canvas2D 渲染器 |
| `frontend/src/utils/webglDetector.ts` | 40 | WebGL 能力检测 |
| `backend/app/routers/system.py` | 39 | GPU 信息端点 |
| `frontend/src/composables/useCanvasTools.ts` | 56 | Canvas2D 测量工具 |
| `frontend/src/composables/useTools.ts` | 163 | Cornerstone3D 工具组 |

### 完整 API 端点清单

| 路由 | 端点数 | 核心端点 |
|------|--------|---------|
| `/api/dicom` | 14 | upload, slice, volume-binary, structs, struct-mask, dose |
| `/api/config` | 4 | CRUD 配置文件 |
| `/api/postprocessing` | 5 | HU→RED, rename-struct, sum-doses |
| `/api/export` | 2 | NRRD 导出 |
| `/api/converter` | 7 | DICOM→NIfTI, anonymize, SSE |
| `/api/annotations` | 3 | save, load, export CSV |
| `/api/dicomweb` | 7 | PACS 连接、QIDO/WADO |
| `/api/anonymization` | 6 | profiles, preview, apply, audit |
| `/api/seg` | 4 | list, check, mask, volume |
| `/api/4d` | 2 | info, volume |
| `/api/analysis` | 1 | 序列分析 |
| `/api/auth` | 5 | login, refresh, me, logout |
| `/api/system` | 1 | gpu-info |
| `/api/logging` | 3 | CRUD 日志 |
| `/api/upload/medical` | 1 | NIfTI/NRRD/MHA 上传 |

**总计**: 15 个路由模块，65 个 API 端点。

---

*文档结束。如有疑问请参考代码注释或项目 README。*
