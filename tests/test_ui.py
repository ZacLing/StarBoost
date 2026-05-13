from starboost.ui import render_export, render_review, render_status


def test_panels_show_path_placeholders_and_clickable_full_path_lines() -> None:
    long_path = "/tmp/" + "very_long_directory_name/" * 8 + "artifact.zip"

    export_panel = render_export({"path": long_path, "bytes": 123})
    review_panel = render_review({"review_path": long_path, "deliverables_path": long_path})
    status_panel = render_status({"package_id": "demo", "status": "awaiting_review", "latest_outputs": long_path})

    assert "..." not in export_panel
    assert "..." not in review_panel
    assert "Directory" in export_panel
    assert "Path               <Path>" in export_panel
    assert "Full paths:" in export_panel
    assert "  Path:\n" in export_panel
    assert long_path in export_panel
    assert "  Review file:\n" in review_panel
    assert "  Deliverables:\n" in review_panel
    assert long_path in review_panel
    assert "  Outputs:\n" in status_panel
    assert long_path in status_panel
    assert ">> Next:" in review_panel
    assert review_panel.rstrip().endswith(">> Next: edit the review file, then type `submit`.")
