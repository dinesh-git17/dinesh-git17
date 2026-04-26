# Dashboard Animation Design

Date: 2026-04-26

## Goal

Add self-contained SVG animation to the GitHub profile dashboard while keeping
the README asset sharp, portable, and calm after load. The animation should make
the dashboard feel like an energetic technical display coming online, then leave
only sparse ambient accents.

## Scope

This spec covers animation generated into `assets/dashboard.svg` by
`scripts/build_dashboard.py`.

In scope:

- A coordinated one-shot load sequence.
- One-shot stats row animation for rings, bars, and numbers.
- One-shot tech stack cascade.
- Sparse idle accents for the name prompt, brain image, and quote icon.
- Tests that preserve existing SVG marker and ID contracts.

Out of scope:

- Clickable SVG links in the GitHub README.
- JavaScript animation.
- External CSS, remote assets, or runtime dependencies.
- New dashboard sections or content changes.
- Raster animation formats such as GIF or video.

## Constraints

GitHub renders the dashboard through Markdown image syntax, so the SVG must work
as a standalone image. Animation must use native SVG elements such as `animate`
and `animateTransform`. The static SVG attributes must remain at their final
values so renderers that ignore animation still show the correct dashboard.

The daily uptime workflow patches marker-bounded text inside
`assets/dashboard.svg`. Existing markers and IDs must remain stable:

- `grade-ring`
- `streak-ring`
- `lang-1-bar` through `lang-5-bar`
- Existing stats and uptime comment markers

## Animation Model

Use small Python helpers in `scripts/build_dashboard.py` to emit repeatable SVG
animation fragments. The helpers should keep animation timing and easing values
centralised enough to tune without searching through every SVG string.

Preferred primitives:

- `animate` for opacity, width, stroke dash values, and filter opacity.
- `animateTransform` for scale or translation where supported cleanly.
- Group-level wrappers for elements that need coordinated opacity and transform.

CSS animation and JavaScript are intentionally avoided.

## Boot Sequence

The boot sequence is coordinated across the dashboard and lasts about
1.7 seconds.

Timeline:

- `0.0s`: final static layout is present.
- `0.1s`: the `>_` prompt beside the name gives a terminal-cursor pulse.
- `0.25s` to `1.15s`: tech stack icons cascade from left to right.
- `0.65s` to `1.55s`: stats row rings, bars, and numbers animate in.
- `1.7s`: load animation is complete and settled.

The sequence feels energetic, but not bouncy enough to read as playful.
Motion stays short, crisp, and data-oriented.

## Stats Row

The stats row uses one-shot load animation only.

`GITHUB AT A GLANCE`:

- Metric rows fade in with a quick stagger.
- The grade ring animates from an empty arc to its final arc.
- The `A` grade fades and scales in after the ring begins moving.

`CONTRIBUTION OVERVIEW`:

- The total contribution number fades and scales in.
- The current streak ring animates from empty to full.
- The current streak `85` pops in after the ring has visible momentum.
- The longest streak `85` follows with a small delay.

`TOP LANGUAGES`:

- Language labels and values fade in with their row.
- Each bar grows from zero to its final width.
- Rows stagger from top to bottom by about 80 to 100 milliseconds.

Final values stay in the base attributes. Animation should not move text enough
to risk clipping in the compact cards.

## Tech Stack

Each tech icon and label pair is emitted as a group. Groups cascade from
left to right during the boot sequence.

Animation behaviour:

- Opacity moves from `0` to `1`.
- Position settles upward by a few pixels, or scale settles gently if transform
  support is cleaner in the generated SVG.
- Stagger stays visible across all icons without delaying the stats row too
  long.

The cascade should read as a polished reveal, not a carousel or attention grab.

## Idle Accents

Idle accents repeat sparsely after the boot sequence. They must not change
layout, block readability, or compete with the stats row.

Name prompt:

- The `>_` prompt beside the name pulses like a terminal cursor.
- Period: about 2 seconds.
- Effect: subtle opacity lift or small fill-intensity change.

Brain image:

- The brain image in the About panel gives a subtle heartbeat pulse.
- Period: about 8 to 10 seconds.
- Effect: slight opacity lift or tiny scale pulse.

Quote icon:

- The quote icon occasionally glows softly.
- Period: about 12 to 16 seconds.
- Effect: subtle opacity and stroke/fill intensity lift.

Idle accents start after the main boot sequence has mostly settled.

## Testing

Tests should stay focused on generated SVG contracts.

Add or update tests to verify:

- Existing stats markers remain present.
- Existing patchable IDs remain present.
- Grade and streak rings include native SVG animation.
- Language bars include native SVG animation.
- Tech stack groups include animation.
- The generated SVG remains a complete document.

No visual regression system is required for this spec, but manual browser
verification should confirm the load sequence and idle accents in
`_preview.html`.

## Acceptance Criteria

- `assets/dashboard.svg` animates in the local preview with the coordinated boot
  sequence.
- The stats row rings, bars, and numbers animate once and settle.
- The tech stack cascades on load.
- The name prompt, brain image, and quote icon have sparse idle accents.
- The SVG remains readable if animation is unsupported.
- The daily uptime patching contract remains unchanged.
- The test suite passes.
