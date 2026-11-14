from datetime import date
from typing import Literal, Protocol
from pydantic import BaseModel, ConfigDict, Field, field_validator
from packages.research.citations import canonical_doi

Topic = Literal['ai', 'data', 'finance', 'math']
Kind = Literal['brief', 'preprint', 'peer-reviewed']


class Source(BaseModel):
    model_config = ConfigDict(extra='forbid')
    authors: str = Field(min_length=2, max_length=500)
    venue: str = Field(min_length=2, max_length=300)
    title: str = Field(min_length=4, max_length=500)
    url: str = Field(min_length=12, max_length=2048)
    doi: str | None = Field(default=None, max_length=255)

    @field_validator('doi')
    @classmethod
    def doi_token(cls, value: str | None) -> str | None:
        return canonical_doi(value) if value is not None else None



class Brief(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(pattern=r'^[a-z0-9][a-z0-9-]{0,79}$')
    topic: Topic
    kind: Kind
    title: str = Field(min_length=8, max_length=200)
    summary: str = Field(min_length=20, max_length=900)
    what: str = Field(min_length=10, max_length=650)
    when: str = Field(pattern=r'^\d{4}(-\d{2}(-\d{2})?)?$')
    why: str = Field(min_length=10, max_length=650)
    context: str = Field(min_length=10, max_length=650)
    action: str = Field(min_length=10, max_length=650)
    result: str = Field(min_length=10, max_length=650)
    formula: str = Field(default='', max_length=300)
    source: Source

    def body(self) -> str:
        return '\n'.join((self.summary, self.what, self.why, self.context, self.action, self.result))


class IssueInput(BaseModel):
    title: str = Field(min_length=4, max_length=150)
    date: date
    article_ids: list[str] = Field(min_length=1, max_length=12)


class EditorialReview(BaseModel):
    source_checked: Literal[True]
    grammar_reviewed: Literal[True]
    rationale: str = Field(min_length=12, max_length=500)


class IssueDecision(BaseModel):
    checksum: str = Field(pattern=r'^[a-f0-9]{64}$')
    note: str = Field(min_length=12, max_length=500)


class Grammar(Protocol):
    def check(self, text: str) -> dict: ...


class ArtifactStore(Protocol):
    def put(self, data: bytes) -> str: ...
    def get(self, checksum: str) -> bytes: ...


class Renderer(Protocol):
    def render(self, title: str, issue_date: str, entries: list[dict], *, draft: bool = True) -> tuple[bytes, int]: ...
