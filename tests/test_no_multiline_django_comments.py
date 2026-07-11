"""Guard against multi-line ``{# … #}`` Django template comments.

Django's ``{# #}`` comment is single-line only: if it spans a newline it is not
recognised as a comment and leaks onto the page as raw text. This has bitten the
project more than once, so this test fails CI whenever such a comment appears —
use ``{% comment %} … {% endcomment %}`` for multi-line notes instead.
"""

import glob
import os
import re

# Matches a full ``{# … #}`` comment (non-greedy, spanning newlines).
_COMMENT_RE = re.compile(r"\{#(?:(?!#\}).)*?#\}", re.DOTALL)

_TEMPLATE_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"
)


def _multiline_comments():
    offenders = []
    for path in glob.glob(os.path.join(_TEMPLATE_ROOT, "**", "*.html"), recursive=True):
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        for match in _COMMENT_RE.finditer(content):
            if "\n" in match.group():
                line = content[: match.start()].count("\n") + 1
                offenders.append(f"{os.path.relpath(path, _TEMPLATE_ROOT)}:{line}")
    return offenders


def test_no_multiline_django_comments():
    offenders = _multiline_comments()
    assert not offenders, (
        "Multi-line {# #} comments render as raw text — use "
        "{% comment %}{% endcomment %} instead:\n  " + "\n  ".join(offenders)
    )
