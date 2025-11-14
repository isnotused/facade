# 幕墙单元件快速生成验证系统 · Streamlit 版本

该项目使用 Streamlit 将 `curtain_wall` 前端控制台完整迁移到 Python Web 应用，保留参数输入、单元生成、结构验证、误差修正、数据关联与操作记录六大模块。所有分析逻辑与数据结构均复用核心算法，便于与原有静态站点保持一致。

## 目录结构

```
facade/
├── app.py                     # Streamlit 主入口
├── data/
│   └── system_dataset.json    # 预置数据集，可通过脚本重新生成
├── core/
│   ├── __init__.py
│   └── analytics.py           # 参数校核、几何生成、结构分析等核心逻辑
├── scripts/
│   └── generate_initial_data.py  # 生成/刷新数据集
├── pyproject.toml             # 依赖声明（兼容 uv / pip）
└── README.md
```

## 环境准备

推荐使用 [`uv`](https://docs.astral.sh/uv/) 管理依赖：

```bash
cd /Users/fuwei/curtain_wall/facade
uv sync
```

若使用 `pip`：

```bash
cd /Users/fuwei/curtain_wall/facade
python3 -m venv .venv
source .venv/bin/activate
pip install streamlit pandas numpy plotly
```

## 运行 Streamlit 控制台

```bash
cd /Users/fuwei/curtain_wall/facade
uv run streamlit run app.py
```

或使用原生 Python：

```bash
python3 -m streamlit run app.py
```

默认会在 `http://localhost:8501` 启动页面，侧边栏可选择预设方案或手动调整参数，主区域会同步生成各项指标与图表，并记录操作历史。

## 更新数据集

如需重新生成数据（例如调整默认参数）：

```bash
cd /Users/fuwei/curtain_wall/facade
uv run python -m facade.scripts.generate_initial_data
```

命令会覆盖 `data/system_dataset.json`，Streamlit 应用刷新后即可读取最新数据。若直接运行脚本，请确保使用 `-m` 方式以正确加载包路径。

## 功能对照

- **参数输入处理**：侧边栏表单 + Radar 图，复用规则评分逻辑。
- **单元件生成**：几何指标、路径权重 Donut 图、动态系数指标。
- **结构验证**：风压/恒载/稳定性指标、应力折线图与节点表格。
- **误差修正**：残余偏差与装配适配度、迭代趋势组合图。
- **数据关联**：阶段关联度柱状图、设计-现场对照表。
- **操作日志**：在 `session state` 中追溯最近 12 次计算记录。

该项目可作为企业内部部署、原型验证或进一步扩展（例如接入真实后台数据、SSO 登录）的基础版本。

