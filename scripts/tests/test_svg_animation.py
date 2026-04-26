"""Tests for the SVG animation primitives module."""

from scripts.lib import svg_animation as anim


def test_boot_animate_emits_animate_element_with_freeze() -> None:
    fragment = anim.boot_animate(
        attribute="opacity",
        from_value="0",
        to_value="1",
        begin_s=0.65,
        dur_s=0.4,
    )
    assert fragment.startswith("<animate ")
    assert 'attributeName="opacity"' in fragment
    assert 'from="0"' in fragment
    assert 'to="1"' in fragment
    assert 'begin="0.65s"' in fragment
    assert 'dur="0.4s"' in fragment
    assert 'fill="freeze"' in fragment
    assert fragment.endswith("/>")


def test_boot_animate_supports_values_list() -> None:
    fragment = anim.boot_animate(
        attribute="opacity",
        values=("0", "1"),
        begin_s=0.0,
        dur_s=0.4,
    )
    assert 'values="0;1"' in fragment
    assert "from=" not in fragment
    assert "to=" not in fragment


def test_boot_transform_emits_animateTransform_with_additive_sum() -> None:
    fragment = anim.boot_transform(
        transform_type="scale",
        from_value="0 1",
        to_value="1 1",
        begin_s=0.7,
        dur_s=0.6,
    )
    assert fragment.startswith("<animateTransform ")
    assert 'attributeName="transform"' in fragment
    assert 'type="scale"' in fragment
    assert 'from="0 1"' in fragment
    assert 'to="1 1"' in fragment
    assert 'begin="0.7s"' in fragment
    assert 'dur="0.6s"' in fragment
    assert 'fill="freeze"' in fragment
    assert 'additive="sum"' in fragment


def test_idle_animate_emits_indefinite_repeat() -> None:
    fragment = anim.idle_animate(
        attribute="opacity",
        values=("1", "0.55", "1"),
        begin_s=2.0,
        dur_s=2.0,
    )
    assert 'attributeName="opacity"' in fragment
    assert 'values="1;0.55;1"' in fragment
    assert 'begin="2s"' in fragment
    assert 'dur="2s"' in fragment
    assert 'repeatCount="indefinite"' in fragment
    assert "fill=" not in fragment


def test_idle_animate_supports_keytimes_for_cadence_control() -> None:
    fragment = anim.idle_animate(
        attribute="opacity",
        values=("1", "0.55", "1"),
        key_times=("0", "0.5", "1"),
        begin_s=2.0,
        dur_s=2.0,
    )
    assert 'keyTimes="0;0.5;1"' in fragment


def test_timing_constants_match_spec_boot_sequence() -> None:
    assert anim.BOOT_PROMPT_BEGIN_S == 0.1
    assert anim.BOOT_TECH_BEGIN_S == 0.25
    assert anim.BOOT_TECH_STAGGER_S == 0.07
    assert anim.BOOT_STATS_BEGIN_S == 0.65
    assert anim.BOOT_STATS_STAGGER_S == 0.09
    assert anim.IDLE_BEGIN_S == 1.8
