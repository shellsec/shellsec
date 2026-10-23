"""Manually refresh public GitHub signals with the authenticated GitHub CLI."""
import datetime as dt
import html
import json
import math
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
QUERY = '''query { user(login:"shellsec") { contributionsCollection {
contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
} repositories(first:100,ownerAffiliations:OWNER,privacy:PUBLIC,orderBy:{field:UPDATED_AT,direction:DESC}) {
nodes { name description url isFork stargazerCount primaryLanguage { name } } } } }'''


def generate(response):
    user = response['data']['user']
    calendar = user['contributionsCollection']['contributionCalendar']
    days = [d for w in calendar['weeks'] for d in w['contributionDays']]
    repos = [r for r in user['repositories']['nodes'] if not r['isFork'] and r['name'] != 'shellsec']
    priority = ['AINav', 'bolemusic', '1panel-upgrade', '1panel_multi_apps_autoupgrade']
    picked = sorted(repos, key=lambda r: (priority.index(r['name']) if r['name'] in priority else 99, -r['stargazerCount']))[:6]
    payload = {'updated': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
               'total': calendar['totalContributions'], 'days': days, 'projects': picked}
    for folder in ['assets', 'site']:
        (ROOT / folder).mkdir(exist_ok=True)
    (ROOT / 'site/data.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    stars = []
    for i, day in enumerate(days):
        a = i * 2.3999632297
        radius = 28 + math.sqrt(i / max(1, len(days) - 1)) * 225
        x, y = 778 + math.cos(a) * radius, 301 + math.sin(a) * radius * .69
        count = day['contributionCount']
        size = 1.2 if not count else min(6, 2 + math.log2(count + 1))
        color = '#32485c' if not count else '#efba78' if count > 8 else '#8ce8ed'
        stars.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{size:.1f}" fill="{color}"><title>{day["date"]}: {count} contributions</title></circle>')
    svg = (ROOT / 'assets/control-template.svg').read_text(encoding='utf-8')
    svg = svg.replace('<!-- STARS -->', ''.join(stars)).replace('TOTALCOUNT', str(payload['total'])).replace('SYNCSTAMP', payload['updated'])
    (ROOT / 'assets/control-center.svg').write_text(svg, encoding='utf-8')
    rows = ['| 项目 | 信号内容 | 语言 | Stars |', '| :-- | :-- | :-- | --: |']
    for repo in picked:
        desc = (repo['description'] or '打开仓库，探索项目。').replace('|', ' / ').replace('\n', ' ')
        lang = (repo['primaryLanguage'] or {}).get('name', '—')
        rows.append(f'| [{repo["name"]}]({repo["url"]}) | {html.escape(desc)} | {lang} | {repo["stargazerCount"]} |')
    template = (ROOT / 'assets/readme-template.md').read_text(encoding='utf-8')
    (ROOT / 'README.md').write_text(template.replace('<!-- PROJECTS -->', '\n'.join(rows)), encoding='utf-8')


if __name__ == '__main__':
    result = subprocess.run(['gh', 'api', 'graphql', '-f', 'query=' + QUERY], check=True, capture_output=True, text=True, encoding='utf-8')
    response = json.loads(result.stdout)
    if response.get('errors'):
        raise RuntimeError(response['errors'])
    generate(response)
