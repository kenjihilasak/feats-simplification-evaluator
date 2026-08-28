"""Shared, versioned values used by the annotation API and exports."""

CAMPAIGN_ID = "v1"
SCHEMA_VERSION = 1

STRATEGIES = ("SYN", "MOD", "COMP", "EXPL", "SYNT", "OMIT")
CORRECTED_STRATEGIES = STRATEGIES + ("NONE", "MULTIPLE", "OTHER")
VERDICTS = ("correct", "incorrect", "uncertain")
ALIGNMENT_JUDGMENTS = ("valid", "invalid")
SEMANTIC_ROLES = (
    "replaced",
    "replacement",
    "modified_source",
    "modified_target",
    "compressed_source",
    "compressed_target",
    "explained",
    "explanation",
    "syntactic_source",
    "syntactic_target",
    "omitted",
    "other",
    # Roles emitted by the versioned strategy guide used by the web client.
    "complex_expression",
    "simpler_equivalent",
    "source_information",
    "redistributed_information",
    "expanded_content",
    "compressed_content",
    "explained_anchor",
    "explanatory_content",
    "source_construction",
    "changed_construction",
    "omitted_content",
)
USER_ROLES = ("reviewer", "admin")
ANNOTATION_STATES = ("draft", "submitted", "skipped")

DEFAULT_LANGUAGE_PRIORITY = ("en", "es", "it", "ru", "ar")
DEFAULT_LEASE_SECONDS = 15 * 60
DEFAULT_SESSION_SECONDS = 12 * 60 * 60
DEFAULT_MAX_ACTIVE_GAP_SECONDS = 5 * 60
MAX_NOTES_LENGTH = 4_000
MAX_IMPORT_BATCH = 1_000
MAX_SKIP_REASON_LENGTH = 500

# These fields are useful to administrators and exports, but would bias a
# reviewer if returned with a task. They are stripped recursively from the
# reviewer-facing metadata object.
BLINDED_METADATA_KEYS = frozenset(
    {
        "model_votes",
        "votes",
        "majority_votes",
        "quality_tier",
        "tier",
        "pool_type",
        "e5_supports_candidate",
        "qwen_supports_candidate",
        "xlmr_supports_candidate",
        "e5_supports_strategy",
        "qwen_supports_strategy",
        "xlmr_supports_strategy",
    }
)
