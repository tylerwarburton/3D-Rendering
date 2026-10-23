# miata-toggle-panel

A draft insert for toggle switches in one Mazda Miata driver-side dashboard
switch position.

The current fit-test revision keeps the source bezel's visible lip, clears the
old rear walls for two 90-degree switch bodies and extends the plug to 23 mm.
The broad switch edges remain uncovered; bottom/top clip walls and a filled
centre column contain two hooked flex tongues per switch. The switches remain
purchased hardware shown only in the browser scene.

Do not print all three yet: the 12.2 mm mounting holes and rear-body envelope
still depend on provisional measurements. Print one fit test first.

```bash
python build.py miata-toggle-panel
pytest projects/miata-toggle-panel -q
```

Output: `out/miata-toggle-panel/stl/two_toggle_panel.stl` (draft only).
