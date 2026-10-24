# miata-toggle-panel - design log

One round per design change, newest first: what Tyler asked, what changed,
why, and how it was checked (tests, numbers, screenshot, test print result).

### Round 48 - clip flush fillers to original rear-shell curvature (2026-10-23)

- Tyler identified F43 and the three matching filler ends as protruding beyond
  the source shell's rounded front/back corner profile.
- Extracted the original STL's rear-band outline, extruded it through the full
  wall depth, and intersected both flush fillers with that envelope.
- The inner wall planes remain flush at x=6.6 and x=43.15, while all four ends
  now follow the source curve instead of terminating as rectangular faces.

### Round 47 - channel walls flush with toggle-mount backs (2026-10-23)

- Tyler selected F41/F42 and requested that their +Z faces be flush.
- Removed the 0.05 mm cutter setback: rear channels and both outer-wall fillers
  now terminate at PANEL_BACK_Z=-0.4 instead of z=-0.45.
- Both toggle sides now meet the mounting-panel back at the same printable
  z=2.4 plane, eliminating the 0.05 mm ledge.

### Round 46 - complete flush outer walls on both sides (2026-10-23)

- Tyler identified F37/F38 and their mirrored counterparts as cap/sloped
  transition surfaces left by the first fillers.
- Extended both fillers across the complete 27.3 mm width and full
  z=-23..-0.45 channel depth.
- Both outer inner walls are now single planes at x=6.6 and x=43.15, with no
  intermediate top, bottom, sloped, or width-transition faces.

### Round 45 - fill original outer indents flush to channel walls (2026-10-23)

- Tyler confirmed that F35 is original geometry but requested that it be filled
  forward until flush with the F36 switch-channel wall.
- Added two symmetric rectangular fillers over the source's 23 x 10.5 mm
  recessed regions, ending exactly at x=6.6 and x=43.15 mm.
- The resulting outer inner faces preserve 0.4 mm clearance around both 16 mm
  front shoulders. Holes, channels, centre divider, and rear depth are unchanged.

### Round 44 - audit back to a minimal original-STL edit (2026-10-23)

- Tyler requested a full audit and removal of every irrelevant wall experiment.
- Rebuilt the generator around the repaired original STL with only five edits:
  rear extension to 23 mm, filled front plate, two 12.2 mm holes, two simple
  switch-body channels, and one straight centre divider.
- Removed all added outside walls, front filler strips, reinforcement steps,
  pillars, flex geometry, relief cuts, and special face transitions.
- The centre divider is exactly the 2.95 mm gap between the 16.8 mm channels,
  leaving 0.4 mm clearance to each 16 mm front shoulder.

### Round 43 - replace four reinforcement pillars with full walls (2026-10-23)

- Tyler identified F31 and three matching 2 x 21 mm faces as the ends of local
  reinforcement pillars that should not exist.
- Extended the rear thick sections across the full original 27.3 mm wall span,
  eliminating the four y-direction pillar transitions.
- The rear outer walls now sit flush to the former F33 body-clearance planes;
  the centre wall is likewise full width between both switches.
- Kept only a short depth-wise step near the face to clear the wider 16 mm
  switch shoulder by 0.4 mm.

### Round 42 - restore wall material in all former flex zones (2026-10-23)

- Tyler requested that every cutout/tab region be returned to plain wall after
  removing the flex system, using the original STL as reference.
- The source rear plug envelope spans y=0..27.3 mm. Extended all three support
  walls from the flex-era 23 mm trim back to that full original span.
- Added solid-volume checks at both former end zones on all three walls, proving
  no flex relief or tab cavity remains.

### Round 41 - remove flex system and keep simple walls (2026-10-23)

- Tyler determined that printed flex clasps are not useful at this scale and a
  separate holder will retain the switches around their circular mounts.
- Removed all eight flex bars, root anchors, end clips, shell relief channels,
  and tab-bite cuts. No replacement clasp or holder was added.
- Retained only the two continuous outside walls and continuous centre wall,
  including their maximum-width reinforced middle sections and body clearance.
- Removed obsolete flex-part names and specifications from the browser scene.

### Round 40 - maximum-width middle sections on all three walls (2026-10-23)

- Tyler clarified that the centre of the internal wall and both outside walls
  should be made as wide as possible, not merely 1.6 mm.
- Expanded each uninterrupted 21 mm middle section to 3.95 mm behind the front
  shoulder, leaving 0.4 mm clearance to the 15 mm switch-body envelope.
- Stepped the front portions to the maximum width that retains the same 0.4 mm
  clearance around the 16 mm-wide shoulder.
- Left every tab-end zone and its flex pocket open and unchanged.

### Round 39 - centre column matches outside wall thickness (2026-10-23)

- Tyler requested a thicker internal wall, with its base and centre matching
  the outside walls.
- Increased the main centre column from 0.85 to 1.6 mm.
- Kept the four centre flex cavities at their established 1.2 mm depth by
  recessing only the tab-width free-length zones. The base and middle remain
  the full 1.6 mm thickness.

### Round 38 - open the four F26-style wall areas (2026-10-23)

- Tyler identified F26 as the large original channel face still present behind
  the outer tabs, with four matching local areas to remove.
- The prior 0.2 mm relief bite stopped 0.05 mm before that face. Increased all
  four outer bites to 0.4 mm, cutting 0.15 mm through the old wall surface.
- Each outer flex bar retains 1.2 mm of its original 1.6 mm thickness.

### Round 37 - reduce outside-tab overhang and bite the bars (2026-10-23)

- Tyler identified F24 and the three matching faces as outer tabs projecting
  too far beyond the fixed wall ends.
- Halved the projection of those four tabs from 1.875 to 0.9375 mm, preserving
  each inner edge so the tabs do not move into the 21 mm body protrusion.
- Narrowed the matching old-shell reliefs with the tabs and extended each relief
  0.2 mm into the flex bar itself. Centre-wall tabs remain unchanged.

### Round 36 - full-length relief behind every flex tab (2026-10-23)

- Tyler used F20/F21 to show that original shell material still interrupted
  the clearance behind the tabs.
- Added eight tab-width relief cuts through only the old shell material, running
  from each anchored root at z=-11.3 to z=-23, 0.5 mm past the free bar end.
- The separate walls, 1.2 mm root anchors, 12.4 mm bars, and retaining clips are
  unchanged; the relief now spans the complete free cantilever length.

### Round 35 - trim wall inserts to the original shell ends (2026-10-23)

- Tyler identified F13/F14 as the end faces of fixed-wall material protruding
  past the original rear shell.
- Reduced all three fixed wall inserts from 27.3 to 23 mm, removing 2.15 mm at
  both ends so their front/back limits match the original straight shell wall.
- Kept the eight corner flex bars, anchors, and clips separate and unchanged.

### Round 34 - remove the source's wider centre rib (2026-10-23)

- Tyler identified F11 and F12 as the two faces of the only centre wall that
  should remain.
- Removed the complete original 2.95 mm-wide rear centre rib while preserving
  the front mounting plate.
- Re-added only the narrow 0.85 mm fixed core between F11/F12, along with its
  four separate flex tabs, front anchors, and end clips.
- Extended that narrow core alone 0.1 mm into the rear of the face plate so the
  centre clips remain part of the printable body after removing the old rib.

### Round 33 - flatten outer wall indents and shorten tabs again (2026-10-23)

- Tyler identified F9 as a recessed outer-wall section beside the main F10
  plane and requested that every equivalent indent be removed.
- Filled the 0.125 mm step on both outer walls only from the rear-shell join to
  the tab starts, producing a continuous front wall plane without filling the
  flex cavities behind the moving bars.
- Shortened all eight flex bars another 3 mm, from 15.4 to 12.4 mm free length.
  Bar thicknesses, end clips, and 1.6/1.2 mm backside gaps remain unchanged.

### Round 32 - restore fixed-wall joins to the rear shell (2026-10-23)

- Tyler identified the unwanted axial cutouts between the fixed-wall bottom
  faces (for example F7) and the original rear-shell top faces (for example F8).
- Extended all three fixed walls from z=-4.1 to z=-2.4, overlapping the source
  shell ledge by 0.1 mm and closing every corresponding 1.6 mm gap.
- Kept all eight flex bars separate, shortened, and unchanged; the 1.6 mm outer
  and 1.2 mm centre backside flex gaps remain open for their full free lengths.

### Round 31 - shorter separate tabs with thickness-matched gaps (2026-10-23)

- Tyler explicitly rejected a U-shaped wall tongue: retain four separate flex
  tabs per toggle with solid walls behind them.
- Removed the bar-sized wall windows from Round 30 and restored solid walls.
- Positioned walls so each open backside gap equals its bar thickness: 1.6 mm
  outside and 1.2 mm at the centre column.
- Moved tab/front-anchor start from z=-4.1 to z=-7.1, shortening every bar by
  3 mm while leaving end clips and the 1.2 mm anchors unchanged.

### Round 30 - bar-sized windows through walls (2026-10-23)

- Tyler selected `centre_column - flat right` and clarified that the wall area
  directly behind every flex bar should be removed completely.
- Cut eight rectangular windows through the supporting walls, each exactly the
  2.6 mm bar width and free length from rear tip to front anchor.
- Preserved the bars, all retaining clips, and their 1.2 mm front anchors.
- Removed the previous local clip-back notches; there are no extra side cuts or
  replacement wall material in the bar windows.

### Round 29 - flatter walls, extra shoulder reveal, thicker bars (2026-10-23)

- Tyler referenced `lower_outer_wall - flat bottom` and asked that all wall
  fronts sit 0.5 mm farther behind the wider 3 mm front shoulder.
- Moved cage/front anchors from z=-3.6 to z=-4.1, increasing the visible
  shoulder reveal without changing the lever holes.
- Kept each main wall as a continuous planar box; the only subtraction is a
  0.8 mm-deep local pocket directly behind each retaining lip.
- Doubled flex-bar thicknesses from 0.8 to 1.6 mm outside and 0.6 to 1.2 mm in
  the centre. Open backside gaps and all eight end clips remain.

### Round 28 - shifted solid walls with freestanding thinner bars (2026-10-23)

- Surface naming revealed that `upper_outer_clip_A` was only the visible front
  object; Tyler wanted the material behind its bar removed, not the clip itself.
- Removed all wall-channel/pocket cutters and restored continuous solid walls.
- Shifted every solid wall face 1 mm farther from the switch, leaving the old
  region genuinely open rather than filling it with replacement geometry.
- Halved flex-bar thicknesses: outer bars 1.6 -> 0.8 mm and centre bars 1.2 ->
  0.6 mm. Clip positions and 1 mm retaining lips remain unchanged.
- Each bar now connects to its wall only through a 1.2 mm-deep front anchor;
  its complete backside is otherwise open.

### Round 27 - named selectable surfaces in the browser (2026-10-23)

- Added a shared `Name surface` viewer tool: click a face to display its stable
  label, generated-STL coordinates, and X/Y/Z surface direction.
- Project scene metadata names the front face, outer lip, both toggle mounts,
  centre column, four flex-bar groups, and all eight individual clip ends.
- Chat `Point` picks now include the same `surface_name`, making references in
  follow-up messages unambiguous even while the hardware view is transformed.

### Round 26 - clear the wider front 3 mm shoulder (2026-10-23)

- Tyler measured the first 3 mm on the face side as 1 mm wider per side than
  the 14 mm base: a 16 mm-wide front shoulder.
- Widened the rear entrance channels to clear that 16 mm envelope plus normal
  fit allowance.
- Moved all added clip walls and their front anchors to z=-3.6, immediately
  behind the shoulder, while retaining the rear snap-lip positions.
- Added a test proving the full 16 x 29 x 3 mm shoulder volume has zero cage
  interference at both switch positions.

### Round 25 - cut the full long backside of each tab (2026-10-23)

- Tyler clarified that the desired relief is along the entire long face of the
  tab opposite the toggle body—not beside it and not only near the end clip.
- Replaced the single combined channel and separate tip pocket with three
  explicit cuts per tongue: one 5 mm-deep full-length backside pocket and two
  independent 1 mm edge slots.
- The front 1.2 mm anchor, bar dimensions, and 1 mm end retaining lip remain
  unchanged.

### Round 24 - shorter retaining lips (2026-10-23)

- Reduced each end clip's inward projection from 1.5 to 1.0 mm.
- Preserved straight-bar thickness/length, 0.8 mm clip height, 1 mm side slots,
  and the new 5 mm behind-clip flex pockets.

### Round 23 - move extra relief behind clip, not beside it (2026-10-23)

- Tyler corrected the previous relief direction: extra material had been
  removed beside the clip instead of directly behind its flex path.
- Restored local side relief from 1.8 to the normal 1.0 mm channel slots.
- Increased flex-direction clearance behind the clip from 4 to 5 mm.
- Extended that behind-clip pocket forward from z=-19.5 to z=-16 mm so the
  end of the bar can swing without bottoming out.
- Clip geometry, bar thickness/length, and front anchors remain unchanged.

### Round 22 - enlarged relief behind clip ends (2026-10-23)

- Tyler asked for more material removed specifically behind the clip near the
  free/top end, beyond the clearance already provided along the bar.
- Kept the 2.5 mm asymmetric channel behind each straight cantilever.
- Added a local 4.0 mm-deep, 1.8 mm-per-side pocket around every retaining lip,
  extending from the open rear to z=-19.5.
- Front anchors, bar thickness, bar length, and seated/back-out clip positions
  remain unchanged.

### Round 21 - straight cantilevers with end-only snap lips (2026-10-23)

- Tyler rejected the triangular wedge running along the middle of each tab and
  asked for a true bar-and-end-clip mechanism.
- Removed every long wedge. Cantilever thickness and length remain unchanged.
- Added a short rectangular 1.5 mm retaining lip only at each free rear/top end.
- Positioned the lip 0.2 mm behind the fully seated switch rear face, so there
  is no positive-volume interference while seated; backing the switch out
  engages four lips and requires the bars to flex.
- Increased asymmetric rearward flex clearance from 1.5 to 2.5 mm.

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
