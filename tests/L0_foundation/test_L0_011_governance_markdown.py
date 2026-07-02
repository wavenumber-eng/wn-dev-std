from __future__ import annotations

from wn_dev_std.governance_markdown import render_governance_markdown


def test_governance_markdown_renders_headings_and_strong_text() -> None:
    html = render_governance_markdown(
        """
        ## API Requirements

        **Requirement**: This must render.
        """.strip()
    )

    assert '<h2 class="dev-std-gov-h dev-std-gov-h2">API Requirements</h2>' in html
    assert '<strong class="dev-std-gov-strong">Requirement</strong>' in html
    assert "## API Requirements" not in html
    assert "**Requirement**" not in html


def test_governance_markdown_renders_tables_lists_and_code() -> None:
    html = render_governance_markdown(
        """
        | Field | Value |
        |-------|-------|
        | Status | Draft |

        - one
        - `two`

        ```text
        value
        ```
        """.strip()
    )

    assert '<table class="dev-std-gov-table">' in html
    assert '<ul class="dev-std-gov-list">' in html
    assert '<code class="dev-std-gov-code-inline">two</code>' in html
    assert '<pre class="dev-std-gov-code-block">' in html
