from __future__ import annotations

from pathlib import Path

PRODUCT_ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = PRODUCT_ROOT / "docs" / "origin-2026-compatibility.md"


def _content() -> str:
    return DOCUMENT.read_text(encoding="utf-8")


def test_document_exists_and_has_2026_title() -> None:
    lines = _content().splitlines()
    assert lines[0] == "# EditaPlot 的 Origin 2026 兼容说明"
    assert sum(line.startswith("# ") for line in lines) == 1
    assert all(line == line.rstrip() for line in lines)
    assert "\t" not in "\n".join(lines)


def test_document_declares_2026_as_the_only_verified_baseline() -> None:
    compact = " ".join(_content().split())
    assert "Origin / OriginPro 2026" in compact
    assert "10.30" in compact
    assert "唯一实机验证" in compact or "唯一实機驗證" in compact


def test_document_describes_the_2026_fix() -> None:
    content = _content()
    for token in (
        "PutWidth",
        "page.resx",
        "page.width",
        "OPJU",
        "PNG、PDF、TIF",
    ):
        assert token in content


def test_document_states_external_python_and_isolated_instance_boundaries() -> None:
    compact = " ".join(_content().split())
    assert "外部 `originpro` 路线仅适用于 Windows" in compact
    assert "默认采用隔离实例策略" in compact
    assert "不需要先打开 Origin" in compact
    assert "`Application` 总是创建新实例" in compact
    assert "`attach_existing`" in compact


def test_document_requires_probe_and_real_output_evidence() -> None:
    content = _content()
    for evidence in (
        "Automation 握手",
        "模板能力探针",
        "OPJU",
        "PNG、PDF、TIF",
        "对象与视觉证据",
        "人工视觉检查",
    ):
        assert evidence in content


def test_document_links_the_relevant_official_technical_sources() -> None:
    content = _content()
    expected = (
        "https://docs.originlab.com/externalpython/",
        (
            "https://docs.originlab.com/com/"
            "difference-of-application-applicationsi-and-applicationcomsi/"
        ),
        "https://www.originlab.com/index.aspx?pid=3325",
        "https://docs.originlab.com/quick-help/why-graph-looks-different-in-2025b/",
    )
    assert all(url in content for url in expected)


def test_document_contains_only_technical_compatibility_information() -> None:
    folded = _content().casefold()
    forbidden = (
        "授权",
        "邮箱",
        "手机号",
        "stargazer",
    )
    assert "这里只判断技术可调用性" in folded
    assert all(token.casefold() not in folded for token in forbidden)
