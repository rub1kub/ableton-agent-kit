"""Backend planning from an observed tools/list, not from brand names or port 9877."""


def plan_backend(tools, live_version=None):
    names = {t if isinstance(t, str) else t["name"] for t in tools}
    # Provider qualification is deliberately left to the caller: ambiguous aliases are unsafe.
    families = []
    if "aa_snapshot" in names:
        families.append("agent-kit LiveMCP extension")
    if "get_session_snapshot" in names and "describe_capabilities" in names:
        families.append("wstierhout-style typed Ableton MCP")
    if "lom_get_object" in names and "render_and_analyze" in names:
        families.append("CanArslanDev-style extended Ableton MCP")
    if not families and "get_session_info" in names:
        families.append("legacy or unidentified Ableton/LiveMCP")
    groups = {
        "overview": ("aa_snapshot", "get_session_overview", "get_session_snapshot", "get_session_info"),
        "parameters": ("aa_parameters", "get_device_parameters", "lom_get_object"),
        "batch_edit": ("aa_set_parameters", "run_batch", "batch"),
        "rendered_audio": ("render_and_analyze", "record_section", "record_audio"),
        "state_diff": ("session_diff", "snapshot"),
        "arrangement": ("create_arrangement_audio_clip", "duplicate_to_arrangement", "build_arrangement"),
        "automation": ("write_arrangement_automation", "record_automation", "write_automation", "write_clip_automation"),
    }
    selected = {role: [name for name in candidates if name in names] for role, candidates in groups.items()}
    return {"families_inferred_from_names": families, "observed_tool_count": len(names),
            "candidate_tools_by_task": selected, "live_version_supplied": live_version,
            "backend_native_verified": False,
            "warnings": ["A listed tool is not proof of runtime support; read its current schema and constraints.",
                         "Do not send one backend's socket payload to another backend.",
                         "Recording-based analysis mutates temporary routing/tracks; inspect restoration semantics.",
                         "Save/open/Collect All need explicit capability verification, regardless of a tool name."]}
