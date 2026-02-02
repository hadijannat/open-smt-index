"""Pydantic models for the SMT Index."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class GitHubVersion(BaseModel):
    """A version found in the GitHub repository."""

    version: str = Field(description="Semver string e.g. '3.0.1'")
    area: Literal["published", "deprecated"] = Field(
        description="Whether found in published/ or deprecated/ directory"
    )
    repo_path: str = Field(description="Path within the repository")
    github_url: str = Field(description="Full GitHub URL to the version folder")


class VersionLinks(BaseModel):
    """Links associated with a template version."""

    pdf: str | None = Field(default=None, description="Link to PDF specification")
    github: str | None = Field(default=None, description="Link to GitHub folder")


class TemplateVersion(BaseModel):
    """A specific version of a template."""

    version: str = Field(description="Semver string e.g. '3.0.1'")
    is_latest: bool = Field(default=False, description="Whether this is the latest version")
    links: VersionLinks = Field(default_factory=VersionLinks)
    github: list[GitHubVersion] = Field(
        default_factory=list, description="GitHub entries for this version"
    )


TemplateStatus = Literal[
    "Published",
    "In Review",
    "In Development",
    "Proposal submitted",
    "unknown",
]


class TemplateRecord(BaseModel):
    """A submodel template with all its versions."""

    id: str = Field(description="Unique identifier: idta-NNNNN, ext-<slug>, or gh-<slug>")
    name: str = Field(description="Human-readable template name")
    idta_number: str | None = Field(default=None, description="IDTA number e.g. '02006'")
    status: TemplateStatus = Field(default="unknown")
    raw_status: str | None = Field(
        default=None, description="Original status text before normalization"
    )
    description: str | None = Field(default=None, description="Template description from IDTA")
    versions: list[TemplateVersion] = Field(default_factory=list)


class IndexSources(BaseModel):
    """Source URLs used to build the index."""

    idta_registered_templates: str = Field(
        default="https://industrialdigitaltwin.org/content-hub/teilmodelle"
    )
    github_submodel_templates: str = Field(
        default="https://github.com/admin-shell-io/submodel-templates"
    )


class SourceProvenance(BaseModel):
    """Provenance information for a single data source."""

    url: str = Field(description="URL of the data source")
    fetched_at: datetime = Field(description="When this source was fetched")
    record_count: int = Field(description="Number of records from this source")


class BuildProvenance(BaseModel):
    """Provenance metadata for the build process."""

    build_started_at: datetime = Field(description="When the build started")
    build_completed_at: datetime = Field(description="When the build completed")
    build_duration_seconds: float = Field(description="Build duration in seconds")
    sources: list[SourceProvenance] = Field(
        default_factory=list, description="Provenance for each data source"
    )
    git_commit: str | None = Field(default=None, description="Git commit hash if available")
    tool_version: str = Field(description="Version of smt-index tool used")


class TemplateIndex(BaseModel):
    """The complete index of submodel templates."""

    schema_version: str = Field(default="1.0")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    sources: IndexSources = Field(default_factory=IndexSources)
    provenance: BuildProvenance | None = Field(
        default=None, description="Build provenance metadata"
    )
    templates: list[TemplateRecord] = Field(default_factory=list)
