# GPU 渲染逻辑现状报告

> 生成时间：2026-05-30

## 一、架构概览

项目有**两个独立的 GPU 检测维度**，彼此完全无关联：

| 维度 | 检测位置 | 检测方式 | 是否被消费 |
|------|---------|---------|-----------|
| **服务端 GPU** | `backend/app/routers/system.py` | `nvidia-smi` 命令行 | **否** — 前端从未调用此端点 |
| **客户端 WebGL** | `frontend/src/utils/webglDetector.ts` | `canvas.getContext('webgl2')` | **是** — 驱动 ViewerView 渲染分支 |

**关键问题**：后端 `/api/system/gpu-info` 是一个孤立的信息端点，前端没有任何组件、store 或 composable 读取它。前后端 GPU 检测完全脱节。

---

## 二、WebGL 可用（正常模式）vs 不可用（降级模式）

### WebGL 可用时（`useCanvasFallback = false`）

渲染引擎：**Cornerstone3D v4.22** — WebGL2 硬件加速

- 三个 `Cornerstone3DViewer` 视口（axial / sagittal / coronal）
- `RenderingEngine` 创建 ORTHOGRAPHIC 视口，通过 `mdh://` volume loader 从 `/api/dicom/volume-binary` 获取原始体积数据
- 测量工具全部可用：Length、Angle、RectangleROI、EllipticalROI、Probe、ArrowAnnotate
- **同步十字线**（CrosshairsTool）跨三视口联动
- 标注事件驱动（`CORNERSTONE_TOOLS_ANNOTATION_ADDED / MODIFIED / REMOVED`）→ 自动刷新测量面板
- 硬件加速窗位调整（`voiRange`）
- WebGL context loss / restore 自动恢复

### WebGL 不可用时（`useCanvasFallback = true`）

渲染引擎：**ImageSliceViewer.vue** — 纯 Canvas2D

- 三个 `ImageSliceViewer` 组件，每个从后端 `/api/dicom/slice/` 获取单张切片的像素数组
- 后端 `image_builder.py` 用 numpy 做窗位处理后返回 `number[][]`
- 前端逐像素手动归一化渲染到 Canvas2D

---

## 三、无 GPU 模式损失的功能清单

| 功能 | WebGL 模式 | Canvas2D 模式 | 损失程度 |
|------|-----------|-------------|---------|
| **测量工具** (Length, Angle, ROI, Probe) | 完整可用 | **不可用** — 工具绑定需要 RenderingEngine | **严重** |
| **同步十字线** | CrosshairsTool 三视口联动 | 仅屏幕空间虚线，无联动 | **严重** |
| **3D 体积渲染 / MPR** | WebGL 纹理加速正交投影 | 仅单层 2D 切片 | **严重** |
| **标注持久化与导出** | 事件驱动标注系统 | 不可用 | **中等** |
| **MeasurementToolbar** | 功能完整 | 仍渲染但**完全失效**（无视口可绑定） | **中等** — 误导性 UI |
| 窗位 / 窗宽调整 | GPU 硬件加速 `voiRange` | 逐像素 CPU 归一化 | 性能下降 |
| 切片滚动 | 流式体积加载 | 单张请求后端 | 响应变慢 |
| 缩放 / 平移 | GPU 纹理变换 | Canvas transform 矩阵 | 基本等价 |
| 方向标签 | Cornerstone3D overlay | ImageSliceViewer 内置 | 等价 |
| RT 结构叠加 | Cornerstone3D overlay | Canvas2D contour/fill | 等价 |
| 截图 | `canvas.toDataURL` | `canvas.toDataURL` | 等价 |
| DICOM 标签查看 | 侧边栏独立于渲染器 | 同左 | 等价 |

**总结**：Canvas2D 降级模式保留了基础的切片浏览能力，但**丧失了所有测量、标注和同步交互功能**——这些是临床放疗计划的核心工作流。MeasurementToolbar 仍然显示在界面上但处于死状态，会给用户造成困惑。

---

## 四、后端 GPU 利用现状

**当前后端零 GPU 计算**。所有服务均为纯 CPU（numpy / scipy / pydicom）：

| 服务 | 计算类型 | GPU 加速潜力 |
|------|---------|------------|
| `image_builder.py` | `np.stack` 体积组装 + `np.clip` 窗位 | **高** — 体积构建和窗位归一化是典型的并行计算 |
| `rt_dose_builder.py` | 剂量网格重采样 + 色图插值 | **高** |
| `seg_service.py` | 位压缩帧的掩码解码 | 中 |
| `dicom_converter_service.py` | SimpleITK 体积装配 + 重采样 | 中 |
| `nifti_service.py` | nibabel / SimpleITK I/O | 低 — I/O 是瓶颈 |

**无 GPU 时后端性能影响**：体积组装（`_build_volume` 中的 `np.stack`）和窗位处理对大体积数据（512x512x500+）可能耗时数秒，但对当前使用场景（单次请求）仍可接受。

---

## 五、核心问题

1. **后端 GPU 检测是死代码** — `/api/system/gpu-info` 端点存在但无人消费，前后端 GPU 状态完全隔离
2. **MeasurementToolbar 在 Canvas2D 模式下仍显示** — 没有根据 `useCanvasFallback` 隐藏，用户看到工具栏但无法使用
3. **Canvas2D 降级缺少用户提示** — 仅有 `Canvas2D` 徽章，未说明哪些功能受限
4. **后端无 GPU 加速路径** — 即使服务器有 GPU，也只用 CPU 处理

---

## 六、涉及文件清单

| 文件 | 角色 |
|------|------|
| `backend/app/routers/system.py` | GPU 信息端点（孤立，未被消费） |
| `frontend/src/utils/webglDetector.ts` | 客户端 WebGL 能力检测 |
| `frontend/src/views/ViewerView.vue` | 主查看器，WebGL / Canvas2D 分支逻辑 |
| `frontend/src/components/viewer/ImageSliceViewer.vue` | Canvas 2D 降级渲染器（480 行） |
| `frontend/src/components/viewer/Cornerstone3DViewer.vue` | WebGL 视口包装器（67 行） |
| `frontend/src/composables/useTools.ts` | 测量工具（Length, Angle, ROI 等） |
| `frontend/src/utils/cornerstoneVolumeLoader.ts` | 自定义 volume loader |
| `backend/app/services/image_builder.py` | 体积构建 + 切片提取（numpy，最强 GPU 候选） |
| `backend/app/services/rt_dose_builder.py` | RT 剂量网格处理（GPU 候选） |
