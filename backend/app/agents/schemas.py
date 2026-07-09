from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.workflow.graph import WorkflowGraph


Severity = Literal["info", "warning", "critical"]
FindingCategory = Literal[
    "documentation",
    "setup",
    "environment",
    "testing",
    "ci_cd",
    "project_structure",
    "security",
    "deployment",
    "portfolio_readiness",
    "maintainability",
]
IssuePriority = Literal["low", "medium", "high"]


class ValidatorOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    issues: list[str] = Field(default_factory=list)
    corrected_graph: WorkflowGraph | None = None


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: FindingCategory
    severity: Severity
    title: str
    description: str
    recommendation: str
    affected_files: list[str] = Field(default_factory=list)
    suggested_issue_title: str | None = None


class RiskFlag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    severity: Severity
    description: str


class RepoAnalyzerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    findings: list[Finding] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    summary: str


class ReadmeReviewerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quality_score: int = Field(ge=0, le=100)
    missing_sections: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    improved_outline: list[str] = Field(default_factory=list)


class IssueDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    body: str
    labels: list[str] = Field(default_factory=list)
    priority: IssuePriority
    acceptance_criteria: list[str] = Field(default_factory=list)


class IssueGeneratorOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issues: list[IssueDraft] = Field(default_factory=list)

    @field_validator("issues")
    @classmethod
    def issue_titles_must_be_unique(cls, issues: list[IssueDraft]) -> list[IssueDraft]:
        titles = [issue.title for issue in issues]
        if len(titles) != len(set(titles)):
            raise ValueError("issue titles must be unique")
        return issues


class LinkedInDraftOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    post_text: str
    hashtags: list[str] = Field(default_factory=list)
    tone: Literal["professional", "technical", "concise"] = "professional"

    @field_validator("post_text")
    @classmethod
    def must_not_claim_published(cls, value: str) -> str:
        lowered = value.lower()
        forbidden = [
            "published this",
            "posted this",
            "auto-published",
            "auto published",
        ]
        if any(phrase in lowered for phrase in forbidden):
            raise ValueError("LinkedIn draft must not claim it was published")
        return value


class ExecutorOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: dict[str, Any]
