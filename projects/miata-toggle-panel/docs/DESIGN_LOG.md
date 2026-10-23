# miata-toggle-panel - design log

One round per design change, newest first: what Tyler asked, what changed,
why, and how it was checked (tests, numbers, screenshot, test print result).

### Round 20 - deeper flex pockets behind all tongues (2026-10-23)

- Tyler asked for more room for each tab to flex backward while the stronger
  1 mm hook passes the switch body.
- Replaced the symmetric wall-wide channel cutters with per-tab asymmetric
  pockets.
- Each pocket now provides 1.5 mm clear travel opposite the hook direction and
  0.2 mm clearance toward the switch, while retaining the 1.2 mm front anchor
  and 1 mm side relief slots.

### Round 19 - narrower body and stronger forward hooks (2026-10-23)

- Tyler confirmed the 12.2 mm lever hole is correct.
- Reduced provisional rear base width from 15 to 14 mm.
- Halved the protrusion amount: centred envelope reduced from 17 to 15 mm,
  leaving 0.5 mm protrusion per side instead of 1 mm.
- Preserved the centred 21 mm protrusion length and all eight corner tabs.
- Kept tongue thicknesses but doubled hook interference from 0.50 to 1.00 mm.
- Moved the hook peak from the rear body entrance to z=-14 mm, roughly 6 mm
  closer to the printed face, and extended its forward release to z=-10 mm.

### Round 18 - four corner clips per toggle (2026-10-23)

- Tyler increased retention from two to four clips per toggle.
- Added low- and high-end tongues to each outside wall and both switch-facing
  sides of the centre column: eight independent hooked tongues total.
- Every tongue remains 2.6 mm wide and entirely inside one of the confirmed
  4 mm plain-base zones, clear of the centred 21 mm protrusion.
- Updated verification to require exactly four positive-volume hook contacts
  on each switch envelope.

### Round 17 - stepped walls and stronger base-grip tabs (2026-10-23)

- Tyler confirmed the centred protrusion is 21 mm long, leaving accurate 4 mm
  plain-base zones at the ends of the 29 mm body.
- Fixed wall faces remain 0.05 mm from the 17 mm protrusion envelope. Tabs are
  offset into opposite end zones and step 1 mm inward to the 15 mm base.
- Reduced tongue width from 6 to 2.6 mm so each fits fully inside a 4 mm zone.
- Increased outer tongue thickness from 1.2 to 1.6 mm and centre tongues from
  0.8 to 1.2 mm.
- Lengthened the free cantilever by moving its front anchor from 2.0 to 1.2 mm.
- Increased hook interference to 0.50 mm and lengthened the forward release
  ramp to 3 mm, making the base overlap visually and mechanically substantial.
- Updated scene hardware to show the 21 mm centred protrusion.

### Round 16 - walls pulled inside original footprint and flush (2026-10-23)

- Tyler identified that the new transverse walls extended past the original
  plug's side-wall edges and sat too far from the switch bodies.
- Reduced every added bottom/top/centre wall to the source plug's exact 27.3 mm
  width; purchased switch bodies may overhang the open sides, printed walls do not.
- Pulled bottom/top fixed faces from 0.15 to 0.05 mm clearance.
- Widened the centre wall to the complete 2.75 mm gap so its fixed faces sit
  flush against both provisional body envelopes outside the tongue channels.
- Hook projection automatically reduced from 0.25 to 0.15 mm, preserving the
  requested 0.10 mm interference while keeping the wall footprint tighter.

### Round 15 - open switch edges and fuller centre column (2026-10-23)

- Removed the long walls along the switches' 29 mm faces to avoid fitment
  problems if the provisional body measurement is slightly wrong.
- Kept the full-width bottom and top clip walls and their U-channel tongues.
- Widened the centre wall from 2.45 to 2.65 mm, filling nearly the complete
  2.75 mm gap between the body envelopes while preserving its two independent
  tongue channels.
- Switch broad edges are now completely exposed; retention comes only from the
  four requested flex clips plus the front washer/nut.

### Round 14 - hooked tongues inside visible wall channels (2026-10-23)

- Tyler clarified that a clip must be a tongue cut into a solid wall, not a
  freestanding bowed wall.
- Built full-width bottom, top, and centre walls. Each tongue sits inside a
  visible U-shaped channel: 0.8 mm relief on both sides, open at the rear, and
  joined to the wall only by a 2 mm front anchor.
- Added a two-way wedge at each free rear tip. Its 0.25 mm projection creates
  about 0.10 mm interference, with sloped faces that force the tongue aside
  when the switch enters or leaves.
- The centre wall contains two tongues at different lateral positions so they
  flex independently. Total remains four clips: two per toggle.

### Round 13 - opposed switch orientation (2026-10-23)

- Flipped the lower hardware reference to -90 degrees while keeping the upper
  at +90 degrees.
- Each switch's odd side-middle terminal now faces outward: down on the lower
  switch and up on the upper switch.
- Confirmed the printed clip layout matches that intent: one outer flex clip at
  the bottom, one at the top, and two independent centre-column clips between
  the switches (two flex clips per toggle).
- Printable geometry did not otherwise change in this round.

### Round 12 - clips moved to short walls and centre column (2026-10-23)

- Tyler corrected the retention layout: the stretched 29 mm walls should be
  rigid; clips belong on the centre column and the two shorter, thicker walls.
- Restored each long wall as one continuous bearing surface overlapping the
  retained original shell.
- Replaced both outer walls with 1.2 mm cantilevers that bow inward toward the
  switches and have relaxed rear lead-ins.
- Split the centre column into a 0.65 mm fixed core and two independent 0.8 mm
  cantilevers separated from the core by 0.10 mm slots. Each switch therefore
  has its own centre clip plus one outer clip.
- All four clips bow 0.25 mm inward for about 0.10 mm body interference.

### Round 11 - slotted spring fingers tied into original walls (2026-10-23)

- Tyler identified two problems in the conforming cage: the new walls appeared
  separated from the original walls, and the hidden ribs did not behave or read
  as real flex clips.
- Split each long cradle wall into two fixed 5.45 mm strips plus a 6 mm spring
  finger separated by 1 mm relief slots.
- The fixed strips overlap the retained original end/centre walls by about
  0.5 mm, while the complete result remains one connected watertight body.
- Each cantilever is 0.8 mm thick, anchored at the front, relaxed at its rear
  entry edge, and bowed 0.25 mm inward just ahead of the tip. Insertion pushes
  it outward; it springs back with about 0.10 mm friction interference.
- Rear snap nubs and washer/nut retention remain in place.

### Round 10 - conforming four-sided switch cradles (2026-10-23)

- Tyler observed that the deep open cage did not look like it touched or held
  the switch bodies; only the small rear nubs made intentional contact.
- Tightened running clearance from 0.45 to 0.15 mm around the rotated 17 x 29
  mm envelope.
- Added two 0.8 mm flexible walls along the 29 mm faces of each switch. Their
  outside surfaces remain within the original 31.3 mm front-lip footprint.
- Added paired mid-depth friction ribs with 0.10 mm interference so each body
  is visibly and mechanically cradled on four sides.
- Kept the rear snap nubs and the threaded washer/nut as primary retention.

### Round 9 - deep open cage around rotated switches (2026-10-23)

- Preserved the downloaded visible outer lip and complete x/y footprint.
- Stretched the source's rear-most profile from 18.5 to 23 mm deep.
- Cut two 17.8 x 29.8 mm channels through the old rear walls, stopping behind
  the 2.4 mm front panel, so the rotated switch bodies can occupy that space.
- Added one rigid centre guide and two 0.8 mm flexible outer arms. Small rear
  nubs use 0.10 mm interference to steady/catch the bodies; the threaded
  washer and nut remain the primary retention.
- Left the rear open beyond the 20 mm bodies for the three 8 mm terminals and
  wiring. This is a single fit-test revision, not approval to print all three.

### Round 8 - 90-degree two-switch fit trial (2026-10-23)

- Rotated both complete switch references 90 degrees about their threaded
  mounting axes and made both visible in the browser scene.
- This turns the provisional 29 mm rear-body height sideways, leaving the two
  bodies vertically separated at the current centres.
- The 29 mm horizontal body width overlaps the bezel's narrower rear cavity;
  a three-quarter camera and translucent contrasting switches make that
  interference visible.
- Tradeoff shown explicitly: rotating the complete switches also makes their
  lever throw left/right instead of the requested up/down.
- Printable geometry remains unchanged pending Tyler's visual decision.

### Round 7 - corrected back to lever toggles (2026-10-23)

- Corrected a bad interpretation: 29 mm was rendered as a visible rocker face,
  making the switches far too long and changing the switch type.
- Restored lever-style toggle hardware on the visible front: round washer,
  hex nut, pivot, and metal lever. The rectangular envelope stays behind.
- Each switch now contains exactly three rear blades: top, bottom, left-middle.
- Only the lower switch is initially visible, tilted to DOWN-ON so its lever
  reads clearly face-on. The upper UP-ON switch remains in the sidebar,
  initially dimmed, so two overlapping bodies cannot be mistaken for one
  five-prong switch.
- Rear-body measurements remain provisional; the mounting bushing diameter is
  still the original 12 mm assumption and must be measured before printing.

### Round 6 - browser-only switch orientation preview (2026-10-23)

- Added two measured switch references as hidden scene assets, not printable
  parts or download links.
- The switches are independently toggleable in the browser sidebar.
- The lower switch is shown in neutral and the upper switch in an ON position;
  both throw vertically with their 15 x 29 mm faces toward the driver.
- Rear terminal layout corrected from Tyler's measurement: top centre, bottom
  centre, and left-middle; each extends 8 mm behind the 20 mm body.
- The two measured 29 mm faces intentionally show their overlap at the current
  19.75 mm centres so fit can be evaluated after orientation is confirmed.

### Round 5 - actual switch envelope and scene-only rule (2026-10-23)

- Tyler clarified that the switches are purchased hardware. Their geometry
  must be a scene-only reference, never a downloadable printable STL.
- Removed `preview_installed_toggles` from the printable parts list.
- Reported switch dimensions: 15 mm front width, about 17 mm at the side clip
  starting 3 mm behind the front, about 29 mm reported height, 20 mm body
  depth, and three terminals extending another 8 mm.
- The three terminals are common/input plus two outputs for ON-neutral-ON.
- Blocker: if 29 mm is the front-face height, two vertically stacked switches
  need at least 58 mm. That exceeds both the 53.75 mm bezel and its 41.5 mm
  opening. The dimension axis and required rectangular cutout need confirmation.

### Round 4 - confirmed in-car orientation (2026-10-22)

- Tyler confirmed that the bezel's long side is vertical in the car, placing
  the two switches one above the other.
- The hardware is three-position: upper ON, centre neutral/OFF, lower ON.
- The lever throw must follow the bezel's long vertical axis.
- Hardware bodies and levers are thinner, longer rectangles than the current
  placeholder preview. Geometry changes are waiting on Tyler's measurements.

### Round 3 - installed-toggle site preview (2026-10-22)

- Added a visualization-only assembly with two nominal switches installed.
- Each mock switch shows its rear body, threaded bushing, front washer, hex
  nut, pivot, and lever so the mounting direction is visible.
- Kept `two_toggle_panel` as the only part intended for printing.

### Round 2 - two-toggle test shim (2026-10-22)

- Used the newest matching download; the older same-name file is identical.
- Repaired the source STL's single missing triangle.
- Filled the 41.5 x 24.5 mm front opening with a 2.4 mm panel overlapping the
  existing bezel by 0.25 mm per edge.
- Added two 12.2 mm holes on 19.75 mm centres for assumed 12 mm threaded
  toggle bushings.
- Kept the complete exterior and retention envelope unchanged.
- Oriented the visible face on the print bed.
- Verified that two nominal 18 mm washers do not overlap and two nominal
  12 x 13 x 17 mm switch bodies clear the bezel when correctly oriented.
- Hardware dimensions are assumptions until Tyler measures or test-fits the
  actual toggles.

### Round 1 - project started (2026-10-22)

- Goal: Two standard toggle switches in each of the three driver-side Mazda Miata dashboard switch openings
