"""Build the demo video: synthesised narration over real output.

    /tmp/ttsenv/bin/python video/build.py

Every terminal frame is the tool's actual output, captured into `shots/` by running it against
public repositories and against this repository itself. Nothing is retyped for the camera. The
narration is edge-tts; the last card says so.
"""
import asyncio
import pathlib
import re
import subprocess
import sys

from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).parent
SHOTS = HERE / "shots"
BUILD = HERE / "build"
VOICE = "en-US-AndrewNeural"
W, H, FPS = 1280, 720, 30

SCENES = [
    ("card:title",
     "A package says it supports Python three point nine. Nobody re-derives that number after a "
     "refactor adds a match statement. Pip believes it, installs on three point nine, and a "
     "stranger gets a syntax error that names your file and not the reason."),
    ("card:idea",
     "Runs On reads the code that actually ships and compares it against the floor the package "
     "declares. Eleven constructs, each decidable from the syntax tree alone. Nothing is imported "
     "and nothing is executed."),
    ("term:self",
     "Here it is on itself. Seven shipped files, one promise, nothing broken — and it names the "
     "directory it read, because a report you cannot locate is not a report."),
    ("term:scan",
     "Thirty maintained projects: poetry, rich, requests, black, jinja, urllib3 and the rest. One "
     "thousand and sixty shipped files. Nothing reported broken. That zero is the result that "
     "matters — these projects keep their promises, so a tool with an opinion here would be wrong."),
    ("card:probe",
     "The five guarded findings are the substance. Before writing any of this I probed the idea "
     "with a throwaway script, and it immediately accused black and poetry of importing tomllib "
     "below their floor. Both accusations were false. One is wrapped in a try except ImportError, "
     "the other in a version check. That pair is what the guard analysis was built from."),
    ("term:guarded",
     "So now it finds the same two lines, understands why they are safe, and says which guard "
     "protects each one. Found, understood, and not accused."),
    ("term:removed",
     "And the other direction. Delete poetry's version guard, exactly as a tidy-up commit would, "
     "and the tool speaks: one finding, the file, the line, the version it needs against the "
     "version promised, and a non-zero exit."),
    ("term:floor",
     "The same machinery answers the question a maintainer actually has. Could requests still "
     "claim three point eight? No — six things break, each with its line. Could rich? At three "
     "point eight, yes. At three point seven, seven walrus operators say no."),
    ("card:limits",
     "What it cannot do is printed rather than hidden, and one entry is not hypothetical. The "
     "first time this tool ran under the three point nine it promises, it crashed on ast dot "
     "Match, which does not exist before three point ten. Its own check had been silent, because "
     "a missing attribute is not a syntax error. That is in the README, not quietly fixed."),
    ("card:end",
     "Runs On. Thirty repositories, zero false accusations, and five guards it understood. M I T "
     "licensed, and the narration in this video is synthesised."),
]

CARDS = {
    "title": """<h1>Who re-derives requires-python?</h1>
    <p class=sub>A number in a file that no refactor ever updates.</p>
    <pre>$ grep requires-python pyproject.toml
  requires-python = "&gt;=3.9"

$ grep -rn "match " src/ | head -1
  src/thing.py:41:    match value:

$ pip install thing        # on 3.9 — installs happily
$ python -c "import thing" # SyntaxError</pre>""",
    "idea": """<h1>Runs On</h1>
    <p class=sub>Reads the code that ships and asks whether the declared floor is true.</p>
    <table>
      <tr><td class=no>breaks its promise</td><td>an unguarded construct needs a newer Python</td></tr>
      <tr><td class=ok>guarded</td><td>behind <code>sys.version_info</code>, an import fallback, or <code>TYPE_CHECKING</code></td></tr>
      <tr><td class=no>contradiction</td><td>two different floors declared in two places</td></tr>
      <tr><td class=d>not judged</td><td>will not parse, or declares no floor — with the reason</td></tr>
    </table>
    <p class=foot>No dependencies, no network. Never imports or executes the package under test.</p>""",
    "probe": """<h1>The probe that came first</h1>
    <pre>black:  import tomllib needs 3.11, declares 3.10   ← FALSE
poetry: import tomllib needs 3.11, declares 3.10   ← FALSE</pre>
    <table>
      <tr><td>black</td><td><code>try: import tomllib / except ImportError:</code></td></tr>
      <tr><td>poetry</td><td><code>if sys.version_info &lt; (3, 11):</code></td></tr>
    </table>
    <p class=foot>Two false positives, written down before a line of the tool existed. The guard
    analysis is what they turned into.</p>""",
    "limits": """<h1>What it cannot do</h1>
    <table>
      <tr><td>Reads what ships</td><td>code reached through <code>exec</code>, a plugin or a
        generated file is invisible</td></tr>
      <tr><td>Syntax and imports</td><td>not attribute access — <code>ast.Match</code> crashed this
        tool on the 3.9 it promises, and its own check stayed silent</td></tr>
      <tr><td>Your dependencies</td><td>whether <i>they</i> support your floor is a larger question</td></tr>
      <tr><td>The floor is text</td><td>one computed at build time by a plugin is not seen</td></tr>
    </table>""",
    "end": """<h1>Runs On</h1><p class=sub>Does this actually run on the Python it promises?</p>
    <p class=big>github.com/bisale24-ops/runs-on</p>
    <p class=foot>MIT licensed · 30 tests, no network · planned with the Devpost Learn skill pack ·
    the narration in this video is synthesised, there is no presenter.</p>""",
}

SHELL = {
    "self": ("$ runs-on --repo .", "self.txt", None, None),
    "scan": ("$ ./demo/scan.sh", "scan.txt", None, None),
    "guarded": ("$ runs-on --repo black ; runs-on --repo poetry", "guarded.txt", None, None),
    "removed": ("$ sed -i '/version_info < (3, 11)/,+4c\\import tomllib' src/poetry/utils/_compat.py\n"
                "$ runs-on --repo poetry --quiet ; echo \"exit=$?\"", "removed.txt", None, None),
    "floor": ("$ runs-on --repo requests --floor 3.8 --quiet", "floor.txt", None, None),
}

PAGE = """<!doctype html><meta charset=utf-8><style>
 body {{ margin:0; width:1280px; height:720px; background:#fbfaf7; color:#1a1a18;
   font:20px/1.5 system-ui,-apple-system,sans-serif; display:flex; flex-direction:column;
   justify-content:center; padding:0 64px; box-sizing:border-box; }}
 h1 {{ font-size:40px; margin:0 0 6px; letter-spacing:-.02em; }}
 .sub {{ color:#6b6a64; margin:0 0 26px; font-size:22px; }}
 table {{ border-collapse:collapse; font-size:19px; width:100%; }}
 td, th {{ text-align:left; padding:8px 12px; border-bottom:1px solid #e2e0d8; vertical-align:top; }}
 th {{ font-size:14px; text-transform:uppercase; letter-spacing:.06em; color:#6b6a64; }}
 .ok {{ color:#2f6f45; font-weight:600; }} .no {{ color:#8a5a12; font-weight:600; }}
 .d {{ color:#6b6a64; font-weight:600; }}
 .big {{ font-size:28px; }} .foot {{ color:#6b6a64; font-size:16px; margin-top:22px; }}
 pre {{ font:17px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; background:#fff;
   border:1px solid #e2e0d8; border-left:3px solid #8a5a12; border-radius:10px;
   padding:16px 18px; margin:0; white-space:pre-wrap; }}
 code {{ font-family:ui-monospace,Menlo,monospace; }}
 .term {{ background:#14140f; color:#eceae2; border-radius:12px; padding:22px 24px;
   font:16px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace; white-space:pre-wrap;
   overflow:hidden; height:600px; box-sizing:border-box; }}
 .term b {{ color:#fff; }} .term .g {{ color:#7fc79a; }} .term .a {{ color:#e0b063; }}
 .term .d {{ color:#9a988e; }} .term .p {{ color:#7fc79a; }}
</style>{body}"""


def shell_html(command, source, start, end):
    text = (SHOTS / source).read_text().splitlines()
    if start is None:
        start, end = 0, len(text)
    body = []
    if command:
        for piece in command.split("\n"):
            body.append(f"<span class=p>$</span> <b>{piece.lstrip('$ ')}</b>")
        body.append("")
    for line in text[start:end]:
        escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if re.match(r"^(MATCHES|BROKEN|RENAMED|NOT JUDGED)", line):
            escaped = f"<b>{escaped}</b>"
        elif "broken · " in line or "references ·" in line:
            escaped = f"<span class=g>{escaped}</span>"
        elif line.startswith("      "):
            escaped = f"<span class=d>{escaped}</span>"
        elif line.startswith("  "):
            escaped = f"<span class=a>{escaped}</span>"
        body.append(escaped)
    return f'<div class=term>{chr(10).join(body)}</div>'


def run(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


async def render_frames():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        for name, body in CARDS.items():
            await page.set_content(PAGE.format(body=body))
            await page.screenshot(path=str(BUILD / f"card-{name}.png"))
        for name, (command, source, start, end) in SHELL.items():
            await page.set_content(PAGE.format(body=shell_html(command, source, start, end)))
            await page.screenshot(path=str(BUILD / f"term-{name}.png"))
        await browser.close()


def narrate():
    for index, (_, line) in enumerate(SCENES):
        out = BUILD / f"line-{index:02d}.mp3"
        if not out.exists():
            subprocess.run([sys.executable.replace("python", "edge-tts"), "--voice", VOICE,
                            "--text", line, "--write-media", str(out)], check=True)


def main():
    BUILD.mkdir(exist_ok=True)
    asyncio.run(render_frames())
    narrate()
    segments = []
    for index, (frame, _) in enumerate(SCENES):
        kind, name = frame.split(":")
        image = BUILD / f"{'card' if kind == 'card' else 'term'}-{name}.png"
        audio = BUILD / f"line-{index:02d}.mp3"
        segment = BUILD / f"seg-{index:02d}.mp4"
        run("-loop", "1", "-i", str(image), "-i", str(audio),
            "-filter_complex",
            f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"pad={W}:{H}:(ow-iw)/2:0:color=0xfbfaf7,format=yuv420p[v];"
            f"[1:a]apad=pad_dur=0.8,aresample=48000[a]",
            "-map", "[v]", "-map", "[a]", "-r", str(FPS), "-t", f"{duration(audio) + 0.8:.2f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k", str(segment))
        segments.append(segment)
    listing = BUILD / "segments.txt"
    listing.write_text("".join(f"file '{s.name}'\n" for s in segments))
    final = HERE / "runs-on-demo.mp4"
    run("-f", "concat", "-safe", "0", "-i", str(listing),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
        str(final))
    print(f"{final.name}  {duration(final):.1f}s")


if __name__ == "__main__":
    main()
