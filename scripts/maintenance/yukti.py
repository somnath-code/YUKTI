import argparse
from datetime import date
import json
from pathlib import Path

from adapters.ollama.client import Ollama
from adapters.pyspark.bulk import run
from packages.contracts.models import Brief
from packages.core.services import services
from packages.core.settings import ROOT, Settings
from packages.identity.access import Principal
from workers.indexing import index
from workers.ingestion import collect
from workers.publishing import prepare_weekly
from workers.validation import validate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--tenant', default='demo')
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('migrate', 'collect', 'validate', 'seed', 'index'):
        commands.add_parser(name)
    commands.add_parser('draft').add_argument('date', type=date.fromisoformat)
    spark = commands.add_parser('spark')
    spark.add_argument('input', type=Path)
    spark.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.command == 'spark':
        print(json.dumps({'groups': run(args.input, args.output)}))
        return
    settings = Settings()
    deps = services(settings)
    deps.db.migrate()
    if args.command == 'migrate':
        result = {'status': 'migrated'}
    elif args.command == 'collect':
        result = collect(deps.db, deps.artifacts, args.tenant, live=settings.live_feeds)
    elif args.command == 'validate':
        result = validate(deps.db, args.tenant)
    elif args.command == 'index':
        result = index(deps.db, args.tenant, Ollama(settings.ollama_url, settings.model))
    elif args.command == 'draft':
        result = prepare_weekly(deps.editorial, args.tenant, args.date)
    else:
        user = Principal('local:seed', args.tenant, frozenset({'curator'}))
        data = json.loads((ROOT / 'apps/web/public/catalog.json').read_text())
        inserted = 0
        from packages.editorial.service import Problem
        for item in data['articles']:
            try:
                deps.editorial.submit(user, Brief.model_validate(item))
                inserted += 1
            except Problem as exc:
                if exc.code != 409:
                    raise
        result = {'new_drafts': inserted}
    print(json.dumps(result, indent=2))
    if result.get('errors'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
