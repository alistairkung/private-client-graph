"""Backend approval boundary; research availability does not promote a resolver."""
from private_client_graph.pipeline import PipelineConfig


APPROVED_APPLICATION_PIPELINE_CONFIG = PipelineConfig(resolver='none')
