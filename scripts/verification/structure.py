"""Check the repository layout agreed for YUKTI and SUTRA."""
from packages.core.settings import ROOT
from scripts.validation.check_policies import main as verify_policies

DIRECTORIES = {
 'apps': 'web dashboard api admin-console sutra',
 'packages': 'core contracts identity ingestion provenance quality processing research intelligence search editorial language_quality content_policy publishing accessibility',
 'adapters': 'postgres object_storage iceberg pyspark search_engine vector_store ollama identity_provider grammar_checker messaging pdf_renderer',
 'workers': 'ingestion validation indexing inference language_review layout_validation publishing',
 'workflows/airflow': 'dags plugins tests',
 'database': 'migrations schemas seeds',
 'templates/sutra': 'covers layouts styles fonts assets',
 'config': 'sources iam quality editorial publishing search',
 'infrastructure': 'local/docker local/keycloak staging production kubernetes terraform monitoring/prometheus monitoring/grafana monitoring/alerts backup-recovery',
 'security': 'threat-models iam access-policies tenant-isolation incident-response secrets-management supply-chain audit',
 'tests': 'unit integration contract end_to_end data_quality grammar word_count citations pdf_layout accessibility security performance resilience',
 'docs': 'architecture system-design api iam data-governance editorial magazine-design publishing security operations capacity-planning architecture-decisions',
 'data': 'samples',
 'scripts': 'setup validation publishing maintenance verification',
 '.github': 'workflows ISSUE_TEMPLATE',
}
FILES = {
 '': 'README.md LICENSE CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md CHANGELOG.md .gitignore .env.example .editorconfig pyproject.toml uv.lock Makefile compose.yaml',
 'workflows/airflow/dags': 'daily_news.py daily_research.py quality_validation.py weekly_editorial.py weekly_sutra_draft.py',
 'templates/sutra/covers': 'approved-cover.png cover-metadata.yaml',
 'templates/sutra/layouts': 'cover.html masthead.html editorial.html contents.html news-brief.html research-paper.html feature-article.html mathematics.html references.html corrections.html',
 'templates/sutra/styles': 'theme.css typography.css a4-print.css accessibility.css',
 'config/sources': 'official-sources.yaml source-trust-policy.yaml',
 'config/iam': 'roles.yaml permissions.yaml access-policies.yaml',
 'config/quality': 'data-contracts.yaml critical-rules.yaml quality-thresholds.yaml',
 'config/editorial': 'editorial-style-guide.yaml grammar-rules.yaml readability-rules.yaml word-limits.yaml citation-policy.yaml',
 'config/publishing': 'magazine.yaml a4-page-spec.yaml typography.yaml print-quality.yaml weekly-schedule.yaml',
 'config/search': 'ranking.yaml caching.yaml',
 'docs': 'roadmap.md',
 '.github': 'PULL_REQUEST_TEMPLATE.md CODEOWNERS dependabot.yml',
 '.github/workflows': 'ci.yml security.yml data-quality.yml editorial-quality.yml pdf-validation.yml release.yml',
 'docx': 'YUKTI_SUTRA_Platform_Handbook.docx',
}


def main() -> None:
    missing = [str(ROOT / parent / name) for parent, names in DIRECTORIES.items() for name in names.split()
               if not (ROOT / parent / name).is_dir() or not any((ROOT / parent / name).iterdir())]
    missing += [str(ROOT / parent / name) for parent, names in FILES.items() for name in names.split()
                if not (ROOT / parent / name).is_file() or not (ROOT / parent / name).stat().st_size]
    if missing:
        raise SystemExit('Missing or empty paths:\n' + '\n'.join(missing))
    verify_policies()
    print('Requested repository structure verified')


if __name__ == '__main__':
    main()
