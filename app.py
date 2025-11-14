"""Streamlit console replicating the curtain wall unit analytics pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from facade.core import (
    DesignProfile,
    RULE_SET,
    analyze_parameter_integrity,
    build_data_association,
    build_dataset,
    build_profiles,
    compute_error_correction,
    generate_unit_geometry,
    run_structural_verification,
)

DATA_PATH = Path(__file__).parent / "data" / "system_dataset.json"


def load_dataset() -> Dict:
    """Load persisted dataset or fall back to an in-memory build."""

    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text())
    return build_dataset()


def init_session_state(dataset: Dict) -> None:
    """Prepare reusable values in Streamlit's session state."""

    if "history" not in st.session_state:
        st.session_state["history"] = []

    profiles = dataset.get("profiles", [])
    active_id = dataset.get("activeProfileId")
    active_profile = next((item for item in profiles if item["id"] == active_id), profiles[0])

    if "form_profile" not in st.session_state:
        st.session_state["form_profile"] = active_profile
        st.session_state["active_profile_id"] = active_profile["id"]


def profile_to_dataclass(payload: Dict) -> DesignProfile:
    """Convert a payload dictionary to the analytic dataclass."""

    return DesignProfile(
        id=payload.get("id", "CUSTOM"),
        name=payload.get("name", "Custom Scenario"),
        module_width=float(payload["module_width"]),
        module_height=float(payload["module_height"]),
        module_depth=float(payload["module_depth"]),
        curvature_radius=float(payload["curvature_radius"]),
        tilt_angle=float(payload["tilt_angle"]),
        mullion_spacing=float(payload["mullion_spacing"]),
        panel_thickness=float(payload["panel_thickness"]),
        wind_speed=float(payload["wind_speed"]),
        thermal_gradient=float(payload["thermal_gradient"]),
        material=str(payload["material"]),
    )


def render_parameter_form(profiles: List[Dict]) -> Dict:
    """Render sidebar form for parameter manipulation."""

    st.sidebar.header("参数集配置")

    profile_labels = [f"{item['id']} · {item['name']}" for item in profiles]
    active_index = next(
        (index for index, item in enumerate(profiles) if item["id"] == st.session_state["active_profile_id"]),
        0,
    )

    selected_label = st.sidebar.selectbox("方案选择", profile_labels, index=active_index)
    selected_profile = profiles[profile_labels.index(selected_label)]

    if selected_profile["id"] != st.session_state.get("active_profile_id"):
        st.session_state["form_profile"] = selected_profile
        st.session_state["active_profile_id"] = selected_profile["id"]

    with st.sidebar.form("parameter_form"):
        profile_id = st.text_input("方案编号", value=st.session_state["form_profile"]["id"])
        profile_name = st.text_input("方案名称", value=st.session_state["form_profile"]["name"])

        module_width = st.number_input(
            "单元宽度 (m)",
            min_value=float(RULE_SET["module_width"]["min"]),
            max_value=float(RULE_SET["module_width"]["max"]),
            value=float(st.session_state["form_profile"]["module_width"]),
            step=0.01,
        )
        module_height = st.number_input(
            "单元高度 (m)",
            min_value=float(RULE_SET["module_height"]["min"]),
            max_value=float(RULE_SET["module_height"]["max"]),
            value=float(st.session_state["form_profile"]["module_height"]),
            step=0.01,
        )
        module_depth = st.number_input(
            "单元厚度 (m)",
            min_value=float(RULE_SET["module_depth"]["min"]),
            max_value=float(RULE_SET["module_depth"]["max"]),
            value=float(st.session_state["form_profile"]["module_depth"]),
            step=0.001,
            format="%.3f",
        )
        curvature_radius = st.number_input(
            "曲率半径 (m)",
            min_value=float(RULE_SET["curvature_radius"]["min"]),
            max_value=float(RULE_SET["curvature_radius"]["max"]),
            value=float(st.session_state["form_profile"]["curvature_radius"]),
            step=1.0,
        )
        tilt_angle = st.number_input(
            "倾角 (°)",
            min_value=float(RULE_SET["tilt_angle"]["min"]),
            max_value=float(RULE_SET["tilt_angle"]["max"]),
            value=float(st.session_state["form_profile"]["tilt_angle"]),
            step=0.1,
        )
        mullion_spacing = st.number_input(
            "竖梃间距 (m)",
            min_value=float(RULE_SET["mullion_spacing"]["min"]),
            max_value=float(RULE_SET["mullion_spacing"]["max"]),
            value=float(st.session_state["form_profile"]["mullion_spacing"]),
            step=0.01,
        )
        panel_thickness = st.number_input(
            "面板厚度 (m)",
            min_value=float(RULE_SET["panel_thickness"]["min"]),
            max_value=float(RULE_SET["panel_thickness"]["max"]),
            value=float(st.session_state["form_profile"]["panel_thickness"]),
            step=0.001,
            format="%.3f",
        )
        wind_speed = st.number_input(
            "设计风速 (m/s)",
            min_value=20.0,
            max_value=60.0,
            value=float(st.session_state["form_profile"]["wind_speed"]),
            step=1.0,
        )
        thermal_gradient = st.number_input(
            "温差梯度 (°C)",
            min_value=0.0,
            max_value=30.0,
            value=float(st.session_state["form_profile"]["thermal_gradient"]),
            step=0.5,
        )
        material = st.selectbox(
            "材料类型",
            options=["aluminum", "glass", "steel"],
            index=["aluminum", "glass", "steel"].index(st.session_state["form_profile"]["material"]),
        )

        submitted = st.form_submit_button("执行生成/验证")

    updated_profile = {
        "id": profile_id or "CUSTOM",
        "name": profile_name or "自定义方案",
        "module_width": module_width,
        "module_height": module_height,
        "module_depth": module_depth,
        "curvature_radius": curvature_radius,
        "tilt_angle": tilt_angle,
        "mullion_spacing": mullion_spacing,
        "panel_thickness": panel_thickness,
        "wind_speed": wind_speed,
        "thermal_gradient": thermal_gradient,
        "material": material,
    }

    st.session_state["form_profile"] = updated_profile

    return {"payload": updated_profile, "submitted": submitted}


def render_integrity_section(integrity: Dict) -> None:
    st.subheader("参数输入处理与完整性校核")
    col_a, col_b, col_c = st.columns([1, 1, 2])
    col_a.metric("参数完整度", f"{integrity['completenessScore']} %")
    col_b.metric("规则匹配度", f"{integrity['ruleMatchScore']} %")
    col_c.write(integrity["notes"])

    radar_fig = go.Figure()
    values = list(integrity["normalizedIndicators"].values())
    labels = [label.replace("_", " ") for label in integrity["normalizedIndicators"].keys()]
    values.append(values[0])
    labels.append(labels[0])
    radar_fig.add_trace(
        go.Scatterpolar(r=values, theta=labels, fill="toself", name="指标归一化趋势", line=dict(color="#2563EB"))
    )
    radar_fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
    st.plotly_chart(radar_fig, use_container_width=True)


def render_geometry_section(geometry: Dict) -> None:
    st.subheader("单元件生成与几何指标")
    col1, col2, col3 = st.columns(3)
    col1.metric("投影面积 (㎡)", geometry["projectedArea"])
    col2.metric("包络体积 (m³)", geometry["envelopeVolume"])
    col3.metric("框架重量 (kN)", geometry["frameWeight"])

    donut = go.Figure(
        data=[
            go.Pie(
                labels=["构造域", "包络调控", "受力均衡", "厚度调节"],
                values=geometry["pathWeights"],
                hole=0.55,
                textinfo="label+percent",
            )
        ]
    )
    donut.update_layout(showlegend=False)

    st.plotly_chart(donut, use_container_width=True)

    st.markdown("**动态组合系数**")
    coeff_cols = st.columns(4)
    for column, (label, value) in zip(coeff_cols, geometry["dynamicCoefficients"].items()):
        column.metric(label.replace("_", " ").title(), value)


def render_structural_section(structural: Dict) -> None:
    st.subheader("结构验证与应力对比")
    col1, col2, col3 = st.columns(3)
    col1.metric("风压 (kPa)", structural["windPressure"])
    col2.metric("恒载 (kN)", structural["deadLoad"])
    col3.metric("稳定性指数", structural["stabilityIndex"])

    stress_df = pd.DataFrame(structural["stressDistribution"])
    line_fig = go.Figure()
    line_fig.add_trace(
        go.Scatter(
            x=stress_df["node"],
            y=stress_df["generated"],
            mode="lines+markers",
            name="生成应力",
            line=dict(color="#2563EB"),
        )
    )
    line_fig.add_trace(
        go.Scatter(
            x=stress_df["node"],
            y=stress_df["optimized"],
            mode="lines+markers",
            name="优化应力",
            line=dict(color="#14B8A6"),
        )
    )
    line_fig.update_layout(xaxis_title="节点", yaxis_title="应力 (kN)", legend=dict(orientation="h", yanchor="bottom"))
    st.plotly_chart(line_fig, use_container_width=True)

    st.dataframe(stress_df[["node", "elevation", "generated", "optimized"]].head(), use_container_width=True)


def render_correction_section(corrections: Dict) -> None:
    st.subheader("误差修正迭代")
    col1, col2 = st.columns(2)
    col1.metric("残余偏差 (mm)", corrections["residualDeviation"])
    col2.metric("装配适配度", corrections["assemblySuitability"])

    iter_df = pd.DataFrame(corrections["iterations"])
    combo_fig = go.Figure()
    combo_fig.add_trace(
        go.Scatter(
            x=iter_df["iteration"],
            y=iter_df["deviationMm"],
            mode="lines+markers",
            name="尺寸偏差 (mm)",
            line=dict(color="#2563EB"),
        )
    )
    combo_fig.add_trace(
        go.Bar(
            x=iter_df["iteration"],
            y=iter_df["shapeOffsetDeg"],
            name="形态偏移 (°)",
            marker=dict(color="#0EA5E9"),
            opacity=0.7,
        )
    )
    combo_fig.update_layout(xaxis_title="迭代轮次", yaxis_title="偏差值", legend=dict(orientation="h"))
    st.plotly_chart(combo_fig, use_container_width=True)

    st.dataframe(iter_df, use_container_width=True)


def render_association_section(association: Dict) -> None:
    st.subheader("数据关联与同步时序")
    corr_df = pd.DataFrame(association["correlations"])
    bar_fig = go.Figure()
    bar_fig.add_trace(
        go.Bar(
            x=corr_df["stage"],
            y=corr_df["correlation"],
            marker=dict(color="#38BDF8"),
            name="设计-施工关联度",
        )
    )
    bar_fig.update_layout(yaxis=dict(range=[0, 1]))
    st.plotly_chart(bar_fig, use_container_width=True)

    linkage_df = pd.DataFrame(association["linkageTable"])
    st.dataframe(linkage_df, use_container_width=True)


def update_history(profile: DesignProfile, structural: Dict, corrections: Dict, remark: str) -> None:
    entry = {
        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "profile": profile.id,
        "stabilityIndex": structural["stabilityIndex"],
        "assemblySuitability": corrections["assemblySuitability"],
        "remark": remark,
    }
    st.session_state["history"] = [entry] + st.session_state["history"][:11]


def render_history() -> None:
    st.subheader("操作记录")
    if not st.session_state["history"]:
        st.info("暂无历史记录。提交参数后将自动生成记录。")
        return
    history_df = pd.DataFrame(st.session_state["history"])
    st.dataframe(history_df, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="幕墙单元件生成验证 · Streamlit 控制台", layout="wide")
    st.title("幕墙单元件快速生成验证系统 · Streamlit 版")
    st.caption("参数管理、生成逻辑、结构验证、误差修正与数据关联五大模块一次性交付。")

    dataset = load_dataset()
    init_session_state(dataset)

    profiles = dataset.get("profiles", build_profiles())
    form_result = render_parameter_form(profiles)
    remark = f"参数重新计算 · {form_result['payload']['name']}"

    if form_result["submitted"] or "latest_result" not in st.session_state:
        profile_dataclass = profile_to_dataclass(form_result["payload"])
        integrity = analyze_parameter_integrity(profile_dataclass)
        geometry = generate_unit_geometry(profile_dataclass)
        structural = run_structural_verification(profile_dataclass, geometry)
        corrections = compute_error_correction(profile_dataclass, geometry)
        association = build_data_association(profile_dataclass, corrections)

        st.session_state["latest_result"] = {
            "profile": profile_dataclass,
            "integrity": integrity,
            "geometry": geometry,
            "structural": structural,
            "corrections": corrections,
            "association": association,
            "remark": remark,
        }

        update_history(profile_dataclass, structural, corrections, remark)

    result = st.session_state["latest_result"]
    render_integrity_section(result["integrity"])
    render_geometry_section(result["geometry"])
    render_structural_section(result["structural"])
    render_correction_section(result["corrections"])
    render_association_section(result["association"])
    render_history()


if __name__ == "__main__":
    main()

