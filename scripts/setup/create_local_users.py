"""Provision local accounts over the Keycloak Admin API without logging credentials."""
import argparse
from getpass import getpass
from urllib.parse import quote, urlsplit
import httpx
from packages.core.settings import policy


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--keycloak', default='http://localhost:8081')
    ap.add_argument('--admin', default='local-admin')
    ap.add_argument('--tenant', default='demo')
    ap.add_argument('--user', required=True)
    ap.add_argument('--role', action='append', choices=tuple(policy('iam')), required=True)
    args = ap.parse_args()
    if urlsplit(args.keycloak).hostname not in {'localhost', '127.0.0.1'}:
        raise SystemExit('Use this helper with a loopback development Keycloak only.')
    password = getpass(f'Password for {args.user}: ')
    if len(password) < 12:
        raise SystemExit('Use at least 12 characters.')
    admin_password = getpass('Local Keycloak admin password: ')
    with httpx.Client(base_url=args.keycloak, timeout=20, trust_env=False) as client:
        res = client.post('/realms/master/protocol/openid-connect/token', data={
            'client_id':'admin-cli','grant_type':'password','username':args.admin,'password':admin_password})
        res.raise_for_status()
        client.headers['Authorization'] = 'Bearer ' + res.json()['access_token']
        base = '/admin/realms/yukti'
        created = client.post(base + '/users', json={'username':args.user, 'enabled':True,
            'firstName':args.user,'lastName':'Local','email':f'{args.user}@example.invalid','emailVerified':True,
            'attributes':{'tenant_id':[args.tenant]},
            'credentials':[{'type':'password','value':password,'temporary':False}]})
        created.raise_for_status()
        identifier = created.headers['Location'].rsplit('/',1)[-1]
        roles = []
        for name in args.role:
            role = client.get(base+'/roles/'+quote(name,safe=''))
            role.raise_for_status()
            roles.append(role.json())
        client.post(base+f'/users/{identifier}/role-mappings/realm', json=roles).raise_for_status()
    print(f'Created {args.user} for tenant {args.tenant}. Use {args.keycloak} to manage the account.')


if __name__ == '__main__':
    main()
