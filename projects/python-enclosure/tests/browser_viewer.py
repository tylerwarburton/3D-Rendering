"""Headless-browser smoke test of the built viewer (not part of pytest).

    python build.py fittings
    python tests/browser_viewer.py [out/fittings_viewer.html]

Opens the viewer in Chromium (playwright), selects the flange, switches to the
gate variant, runs the open/close animation, downloads every piece, the
current-part zip and the All-STLs zip, and checks every STL is watertight.
three.js comes from the CDN unless THREE_JS points at a local copy.
"""
import asyncio
import io
import os
import sys
import tempfile
import zipfile
from pathlib import Path

import trimesh
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]


async def main(page_path):
    tmp = Path(tempfile.mkdtemp(prefix="viewer_"))
    local_three = os.environ.get("THREE_JS")
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
        pg = await b.new_page(viewport={"width": 1400, "height": 860}, accept_downloads=True)
        if local_three:
            await pg.route("**/three.min.js", lambda r: r.fulfill(path=local_three,
                                                                  content_type="application/javascript"))
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(Path(page_path).resolve().as_uri())
        await pg.wait_for_selector('#loading.gone', state='attached', timeout=120000)
        await pg.click('.item[data-name="flange"]'); await pg.wait_for_timeout(1500)
        print('plain print row:', await pg.eval_on_selector_all('[data-dlp]', 'e=>e.map(x=>x.textContent)'))
        await pg.click('#cfg [data-gatev="slide"]'); await pg.wait_for_timeout(2000)
        row = await pg.eval_on_selector_all('[data-dlp]', 'e=>e.map(x=>x.textContent)')
        print('gate print row:', row)
        await pg.click('#bAct'); await pg.wait_for_timeout(5200)
        print('state:', await pg.inner_text('#actDeg'))
        await pg.screenshot(path=str(tmp / 'flange_gate.png'))
        got = []
        for i in range(len(row)):
            async with pg.expect_download() as d:
                await pg.click(f'[data-dlp="{i}"]')
            dl = await d.value; path = tmp / dl.suggested_filename; await dl.save_as(path)
            got.append((dl.suggested_filename, path))
        async with pg.expect_download() as d:
            await pg.click('#bDl')
        dl = await d.value; zp = tmp / dl.suggested_filename; await dl.save_as(zp)
        async with pg.expect_download(timeout=240000) as d:
            await pg.click('#bDlAll')
        dl = await d.value; await dl.save_as(tmp / 'all.zip')
        await b.close()
    bad = 0
    for n, path in got:
        m = trimesh.load(path)
        bad += not m.is_watertight
        print(f"  {n:40s} watertight {m.is_watertight}  {m.extents[0]:.0f}x{m.extents[1]:.0f}x{m.extents[2]:.0f}")
    print('main download zip:', zipfile.ZipFile(zp).namelist())
    z = zipfile.ZipFile(tmp / 'all.zip'); names = z.namelist()
    nb = [n for n in names if not all(x.is_watertight for x in
          trimesh.load(io.BytesIO(z.read(n)), file_type='stl').split(only_watertight=False))]
    print(f"all zip: {len(names)} files, not watertight: {nb or 0}")
    print("page errors:", errs or "none", "| screenshot:", tmp / 'flange_gate.png')
    return 0 if not (errs or bad or nb) else 1


if __name__ == "__main__":
    page = sys.argv[1] if len(sys.argv) > 1 else ROOT.parents[1] / "out" / ROOT.name / "fittings_viewer.html"
    sys.exit(asyncio.run(main(page)))
