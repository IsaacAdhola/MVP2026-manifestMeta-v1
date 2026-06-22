# Root package exports — uses try/except to support both package-import
# and direct sys.path execution contexts (e.g. pytest, agency.py).
try:
    from .MetaMarkCEO import MetaMarkCEO
    from .ResearchAgent import ResearchAgent
    from .AdCopyAgent import AdCopyAgent
    from .ImageCreatorAgent import ImageCreatorAgent
    from .FacebookPolicyAgent import FacebookPolicyAgent
    from .ClientApprovalAgent import ClientApprovalAgent
    from .FacebookManagerAgent import FacebookManagerAgent
except ImportError:
    # Running without a parent package (e.g. pytest in project root)
    from MetaMarkCEO import MetaMarkCEO  # type: ignore[no-redef]
    from ResearchAgent import ResearchAgent  # type: ignore[no-redef]
    from AdCopyAgent import AdCopyAgent  # type: ignore[no-redef]
    from ImageCreatorAgent import ImageCreatorAgent  # type: ignore[no-redef]
    from FacebookPolicyAgent import FacebookPolicyAgent  # type: ignore[no-redef]
    from ClientApprovalAgent import ClientApprovalAgent  # type: ignore[no-redef]
    from FacebookManagerAgent import FacebookManagerAgent  # type: ignore[no-redef]
