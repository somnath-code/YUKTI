from packages.core.settings import POLICIES, policy
from packages.provenance.sources import canonical_url


def main() -> None:
    for key in POLICIES:
        policy(key)
    permitted = set(policy('permissions')['permissions'])
    granted = {permission for roles in policy('iam').values() for permission in roles}
    if permitted != granted:
        raise SystemExit('IAM permissions and role grants disagree')
    for feed in policy('sources')['feeds']:
        canonical_url(feed['url'])
    if policy('schedule')['timezone'] != 'Asia/Kolkata':
        raise SystemExit('Unexpected SUTRA publication timezone')
    print(f'{len(POLICIES)} configuration policies parsed and cross-checked')


if __name__ == '__main__':
    main()
