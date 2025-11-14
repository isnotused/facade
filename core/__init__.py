"""Core analytics utilities for the facade Streamlit project."""

from .analytics import (
    DesignProfile,
    MATERIAL_DENSITY,
    RULE_SET,
    analyze_parameter_integrity,
    build_data_association,
    build_dataset,
    build_profiles,
    compute_error_correction,
    generate_unit_geometry,
    run_structural_verification,
)

__all__ = [
    "DesignProfile",
    "MATERIAL_DENSITY",
    "RULE_SET",
    "analyze_parameter_integrity",
    "build_data_association",
    "build_dataset",
    "build_profiles",
    "compute_error_correction",
    "generate_unit_geometry",
    "run_structural_verification",
]

