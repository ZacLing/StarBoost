from starboost.ui import render_export, render_review


def test_panels_wrap_long_paths_without_ellipsis() -> None:
    long_path = "/tmp/" + "very_long_directory_name/" * 8 + "artifact.zip"

    export_panel = render_export({"path": long_path, "bytes": 123})
    review_panel = render_review({"review_path": long_path, "deliverables_path": long_path})

    assert "..." not in export_panel
    assert "..." not in review_panel
    assert "Directory" in export_panel
    assert "artifact.zip" in export_panel
