from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_release_artifacts_exist_and_mark_alpha_version() -> None:
    required_paths = [
        "VERSION",
        "CHANGELOG.md",
        "RELEASE_NOTES.md",
        "docs/release-checklist.md",
        "docs/v0.1-demo-workflow.md",
        "docs/troubleshooting.md",
        "examples/README.md",
        "examples/demo-research-article.txt",
        "examples/demo-policy-notice.txt",
        "examples/demo-policy-metadata.json",
        "examples/demo-workflow.http",
        "scripts/e2e_demo.py",
        "scripts/e2e_demo.sh",
    ]

    missing = [path for path in required_paths if not (REPO_ROOT / path).is_file()]

    assert missing == []
    assert (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip() == "0.1.0-alpha"
    assert "v0.1.0-alpha" in (REPO_ROOT / "README.md").read_text(encoding="utf-8")


def test_demo_policy_is_clearly_marked_as_fictional_example() -> None:
    demo_policy = (REPO_ROOT / "examples/demo-policy-notice.txt").read_text(encoding="utf-8")

    assert "【示例数据】" in demo_policy
    assert "虚构政策文本" in demo_policy
    assert "不代表真实政策文件" in demo_policy
