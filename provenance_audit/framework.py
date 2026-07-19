"""The four-category channel-provenance assessment framework.

Each category lists the signals it assesses. For every signal we record:
  - detect:    "auto"   = computable from the collected record (see score.py)
               "manual" = requires human verification (the research labor)
  - covered_by: which EXISTING tool/framework already assesses this signal, if any.
               "" means no existing framework covers it -> this is the channel
               framework's unique contribution, and the basis for the
               "covers vs. misses" gap figure on the poster.

This single definition drives both the per-project scorecard and the gap analysis,
so the framework, the data, and the slides stay consistent.
"""

FRAMEWORK = {
    "C1_identity_access": {
        "label": "Identity & access infrastructure",
        "signals": {
            "multi_maintainer":        {"detect": "manual", "covered_by": "Scorecard (Code-Review/Contributors, partial)"},
            "contributing_doc":        {"detect": "auto",   "covered_by": "Scorecard (Contributing, partial)"},
            "governance_doc":          {"detect": "auto",   "covered_by": ""},
            "mfa_on_channel_admins":   {"detect": "manual", "covered_by": ""},
            "channel_admin_transfer":  {"detect": "manual", "covered_by": ""},
        },
    },
    "C2_communication_channels": {
        "label": "Communication channels",
        "signals": {
            "channels_declared":           {"detect": "auto",   "covered_by": ""},
            "channels_documented":         {"detect": "auto",   "covered_by": ""},
            "official_channel_statement":  {"detect": "manual", "covered_by": ""},
            "impersonation_reporting":     {"detect": "manual", "covered_by": ""},
        },
    },
    "C3_knowledge_infra": {
        "label": "Knowledge infrastructure",
        "signals": {
            "security_policy":   {"detect": "auto",   "covered_by": "Scorecard (Security-Policy)"},
            "changelog":         {"detect": "auto",   "covered_by": ""},
            "release_notes":     {"detect": "auto",   "covered_by": ""},
            "disclosure_depth":  {"detect": "manual", "covered_by": ""},
        },
    },
    "C4_distribution_metadata": {
        "label": "Distribution metadata",
        "signals": {
            "has_release":            {"detect": "auto",   "covered_by": ""},
            "archival_doi":           {"detect": "auto",   "covered_by": ""},
            "signed_releases":        {"detect": "manual", "covered_by": "Scorecard (Signed-Releases); Sigstore"},
            "sbom":                   {"detect": "manual", "covered_by": "Scorecard (SBOM); SLSA"},
            "provenance_attestation": {"detect": "manual", "covered_by": "SLSA; Sigstore"},
        },
    },
}


def all_signals():
    for cat_id, cat in FRAMEWORK.items():
        for sig_id, sig in cat["signals"].items():
            yield cat_id, sig_id, sig
