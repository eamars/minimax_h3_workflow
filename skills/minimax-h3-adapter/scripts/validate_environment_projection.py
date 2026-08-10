"""Validate hard environment projection data and its prompt serialization."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml


REQUIRED_PROJECTION_KEYS = {
    "profile_id",
    "source_asset_id",
    "required_landmarks",
    "allowed_features",
    "unknown_features",
    "negative_space_rule",
    "forbidden_inventions_validation_only",
    "prompt_policy",
}
PROMPT_POLICY = "positive_projection_no_negative_inventory"
BOUNDARY_TOKENS = ("partial", "edge", "cropped", "occluded", "unknown", "unshown")
LANDMARK_ALIASES = {
    "full_height_glass_enclosure": ("glass enclosure", "full-height glass enclosure"),
    "hinged_glass_door": ("hinged glass door", "glass door"),
    "dark_tile_wall_grid": ("dark tile grid", "dark tiled wall"),
    "rainfall_shower_head": ("rainfall shower head", "square rainfall head"),
    "handheld_shower_and_vertical_rail": ("handheld shower and rail", "handheld shower and vertical rail"),
    "pink_lit_recessed_shelf": ("pink-lit recessed shelf", "pink lit recessed shelf"),
    "sakura_towel_rail": ("sakura towel rail", "sakura-patterned towel"),
    "dark_tile_floor_and_square_drain": ("dark tiled floor and drain", "dark tile floor and drain"),
    "warm_recessed_ceiling_light": ("warm ceiling light", "warm recessed ceiling light"),
}
STOP_WORDS = {
    "a",
    "an",
    "and",
    "beyond",
    "full",
    "new",
    "of",
    "only",
    "or",
    "other",
    "right",
    "supplied",
    "the",
}
GENERIC_WORDS = {"architecture", "room", "view", "water"}


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def normalize(value: str) -> str:
    value = value.lower().replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", value).strip()


def environment_profile(document: dict) -> dict:
    profile = document.get("environment_profile", document)
    if isinstance(profile, dict) and isinstance(profile.get("environment_profile"), dict):
        profile = profile["environment_profile"]
    if not isinstance(profile, dict):
        raise AssertionError("ENVIRONMENT_PROFILE_MISSING: profile is not an object")
    required = {
        "profile_id",
        "source_asset_id",
        "enforcement",
        "required_landmarks",
        "allowed_features",
        "forbidden_inventions",
        "unknown_features",
        "negative_space_rule",
    }
    missing = sorted(required - set(profile))
    if missing:
        raise AssertionError(f"ENVIRONMENT_PROFILE_MISSING: missing {missing}")
    if profile["enforcement"] != "hard_reference_no_expansion":
        raise AssertionError("ENVIRONMENT_PROFILE_MISSING: hard reference enforcement required")
    for field in ("required_landmarks", "allowed_features", "forbidden_inventions", "unknown_features"):
        values = profile[field]
        if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
            raise AssertionError(f"ENVIRONMENT_PROFILE_MISSING: {field} must be a non-empty string list")
    if not isinstance(profile["negative_space_rule"], str) or not profile["negative_space_rule"].strip():
        raise AssertionError("ENVIRONMENT_PROFILE_MISSING: negative_space_rule is required")
    return profile


def projection_from_packet(packet: dict, profile: dict) -> dict:
    traceability = packet.get("traceability")
    projection = traceability.get("environment_projection") if isinstance(traceability, dict) else None
    if not isinstance(projection, dict):
        raise AssertionError("ENVIRONMENT_PROJECTION_UNTRACEABLE: traceability.environment_projection is required")
    missing = sorted(REQUIRED_PROJECTION_KEYS - set(projection))
    if missing:
        raise AssertionError(f"ENVIRONMENT_PROJECTION_UNTRACEABLE: missing {missing}")
    if projection["profile_id"] != profile["profile_id"]:
        raise AssertionError("ENVIRONMENT_PROJECTION_UNTRACEABLE: profile_id mismatch")
    if projection["source_asset_id"] != profile["source_asset_id"]:
        raise AssertionError("ENVIRONMENT_PROJECTION_UNTRACEABLE: source_asset_id mismatch")
    for field in ("required_landmarks", "allowed_features", "unknown_features", "forbidden_inventions_validation_only"):
        if projection[field] != profile["forbidden_inventions"] if field == "forbidden_inventions_validation_only" else projection[field] != profile[field]:
            raise AssertionError(f"ENVIRONMENT_PROJECTION_UNTRACEABLE: {field} mismatch")
    if projection["negative_space_rule"] != profile["negative_space_rule"]:
        raise AssertionError("ENVIRONMENT_PROJECTION_UNTRACEABLE: negative_space_rule mismatch")
    if projection["prompt_policy"] != PROMPT_POLICY:
        raise AssertionError("ENVIRONMENT_PROMPT_UNSAFE: positive projection policy is required")
    return projection


def forbidden_prompt_terms(features: list[str]) -> set[str]:
    terms: set[str] = set()
    for feature in features:
        normalized = normalize(feature)
        terms.add(normalized)
        words = [word for word in normalized.split() if word not in STOP_WORDS]
        if len(words) == 1 and words[0] not in GENERIC_WORDS:
            terms.add(words[0])
        if len(words) >= 2:
            for index in range(len(words) - 1):
                pair = " ".join(words[index : index + 2])
                if pair not in GENERIC_WORDS:
                    terms.add(pair)
    return {term for term in terms if term and term not in GENERIC_WORDS}


def prompt_contains_landmark(text: str, feature: str) -> bool:
    aliases = LANDMARK_ALIASES.get(feature)
    if aliases is None:
        aliases = (feature,)
    return any(normalize(alias) in text for alias in aliases)


def forbidden_feature_is_negated(text: str, term: str) -> bool:
    """Allow a validation-only exclusion when it is explicitly negated.

    The old check rejected the word ``bathtub`` even in ``never invent a
    bathtub``.  That made the guard unusable with the existing H3 prompt
    template.  It now rejects positive architecture claims while allowing
    explicit exclusions to remain in the prompt.
    """
    for match in re.finditer(re.escape(term), text):
        sentence_start = max(text.rfind(".", 0, match.start()), text.rfind("\n", 0, match.start())) + 1
        context = text[sentence_start : match.start()].strip()
        if re.search(r"(?:never|no|without|avoid|exclude|do not|don't|not)\b[^.]{0,120}\b(?:invent|add|show|introduce|complete|use)\b", context) or re.search(r"(?:never|no|without|avoid|exclude|do not|don't|not)\s+(?:a|an|the|any)?\s*$", context):
            continue
        return False
    return True


def validate_prompt_text(prompt: str, profile: dict) -> None:
    if not isinstance(prompt, str) or not prompt.strip():
        raise AssertionError("ENVIRONMENT_PROMPT_UNSAFE: prompt is empty")
    text = normalize(prompt)
    if normalize(profile["profile_id"]) not in text:
        raise AssertionError("ENVIRONMENT_PROMPT_UNSAFE: profile_id is absent from prompt")
    for feature in profile["required_landmarks"]:
        if not prompt_contains_landmark(text, feature):
            raise AssertionError(f"ENVIRONMENT_PROMPT_UNSAFE: missing positive landmark {feature}")
    if not any(token in text for token in BOUNDARY_TOKENS[:4]):
        raise AssertionError("ENVIRONMENT_PROMPT_UNSAFE: boundary or occlusion language is required")
    if not any(token in text for token in BOUNDARY_TOKENS[4:]):
        raise AssertionError("ENVIRONMENT_PROMPT_UNSAFE: unknown-space language is required")
    hits = sorted(
        term
        for term in forbidden_prompt_terms(profile["forbidden_inventions"])
        if term in text and not forbidden_feature_is_negated(text, term)
    )
    if hits:
        raise AssertionError(
            "ENVIRONMENT_PROMPT_UNSAFE: forbidden inventions must remain validation metadata only: "
            + ", ".join(hits)
        )


def validate_packet(packet: dict, prompt: str, profile_document: dict) -> None:
    profile = environment_profile(profile_document)
    projection_from_packet(packet, profile)
    visual = packet.get("fields", {}).get("visual")
    if not isinstance(visual, str):
        raise AssertionError("ENVIRONMENT_PROMPT_UNSAFE: fields.visual is required")
    validate_prompt_text(visual, profile)
    validate_prompt_text(prompt, profile)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment-profile", type=Path, required=True)
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--prompt", type=Path)
    args = parser.parse_args()
    if args.packet is None and args.prompt is None:
        raise AssertionError("ENVIRONMENT_PROMPT_UNSAFE: packet or prompt is required")
    profile_document = load(args.environment_profile)
    packet = load(args.packet) if args.packet else None
    prompt = args.prompt.read_text(encoding="utf-8") if args.prompt else None
    if packet is not None:
        validate_packet(packet, prompt or packet.get("fields", {}).get("visual", ""), profile_document)
    else:
        validate_prompt_text(prompt or "", environment_profile(profile_document))
    print("Validated hard environment projection")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
        print(f"Validation failed: {exc}")
        raise SystemExit(1) from exc
