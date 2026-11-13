"""Browser-only helpers (the pygbag build). Everything here does nothing on desktop."""

import json
import sys

IN_BROWSER = sys.platform == "emscripten"


def download_text(filename: str, text: str) -> bool:
    """Make the browser download `text` as a file. Returns False outside the browser."""
    if not IN_BROWSER:
        return False
    import platform  # pygbag's version, which gives access to the page's JavaScript

    script = (
        "(function(){"
        f"const blob = new Blob([{json.dumps(text)}], {{type: 'text/markdown'}});"
        "const a = document.createElement('a');"
        "a.href = URL.createObjectURL(blob);"
        f"a.download = {json.dumps(filename)};"
        "document.body.appendChild(a); a.click(); a.remove();"
        "})()"
    )
    platform.window.eval(script)
    return True
