# pipeline/pipeline_a.py
# Pipeline A stub — interface definition for Phase 4 implementation.
# ============================================================================

from pathlib import Path


class PipelineA:
    """
    Pipeline A — ingestion of FatturaXML files.

    Full implementation in Phase 4.
    This stub satisfies the import contract required by the Scanner page CTA button.
    It must NOT raise on import — only process_folder() raises NotImplementedError.
    """

    def process_folder(self, client_folder: Path) -> None:
        """
        Process all FatturaXML files in a previously scanned client folder.

        Placeholder — Phase 4 will implement:
        - Find all FatturaXML files from scan_results
        - Parse each via FatturaPAParser
        - Generate prima nota suggestions
        - Store results for UI review workflow
        """
        raise NotImplementedError(
            "PipelineA.process_folder() is not yet implemented. "
            "See Phase 4 for full implementation."
        )
