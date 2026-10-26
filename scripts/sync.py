"""Manually refresh public GitHub signals with the authenticated GitHub CLI."""
import datetime as dt
import html
import json
import math
from pathlib import Path
import subprocess
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
QUERY = '''query($cursor:String) { user(login:"shellsec") { contributionsCollection {
contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
} repositories(first:100,after:$cursor,ownerAffiliations:OWNER,privacy:PUBLIC,orderBy:{field:UPDATED_AT,direction:DESC}) {
pageInfo { hasNextPage endCursor }
nodes { name description url homepageUrl pushedAt isFork stargazerCount primaryLanguage { name }
latestRelease { tagName url } } } } }'''


def web_url(value):
    parsed = urlsplit(value or '')
    return value if parsed.scheme in ('https', 'http') and parsed.netloc else None


def cell(value):
    return html.escape(str(value)).replace('|', '&#124;').replace('\n', ' ').replace('\r', ' ')


def generate(response):
    user = response['data']['user']
    calendar = user['contributionsCollection']['contributionCalendar']
    days = [d for w in calendar['weeks'] for d in w['contributionDays']]
    repos = [r for r in user['repositories']['nodes'] if not r['isFork'] and r['name'] != 'shellsec']
    catalog = json.loads((ROOT / 'assets/projects.json').read_text(encoding='utf-8'))
    by_name = {repo['name']: repo for repo in repos}
    picked = []
    for entry in catalog:
        if entry['name'] in by_name:
            repo = dict(by_name[entry['name']])
            repo.update(entry)
            repo['homepageUrl'] = web_url(repo.get('homepageUrl'))
            picked.append(repo)
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
    rows = []
    for category in dict.fromkeys(repo['category'] for repo in picked):
        rows.extend([f'### {category}', '', '| 项目 / 用途 | Stars | 最近推送 | 版本 / 入口 |', '| :-- | --: | :-- | :-- |'])
        for repo in (r for r in picked if r['category'] == category):
            release = repo.get('latestRelease')
            links = []
            if release:
                links.append(f'[{cell(release["tagName"])}]({release["url"]})')
            if repo['homepageUrl']:
                label = '下载' if '/releases' in repo['homepageUrl'] else '访问'
                links.append(f'[{label}]({repo["homepageUrl"]})')
            if not links:
                links.append(f'[使用说明]({repo["url"]}#readme)')
            date = (repo.get('pushedAt') or '')[:10] or '—'
            rows.append(f'| [{cell(repo["name"])}]({repo["url"]})<br>{cell(repo["summary"])} | {repo["stargazerCount"]} | {date} | {" · ".join(links)} |')
        rows.append('')
    template = (ROOT / 'assets/readme-template.md').read_text(encoding='utf-8')
    (ROOT / 'README.md').write_text(template.replace('<!-- PROJECTS -->', '\n'.join(rows)), encoding='utf-8')


if __name__ == '__main__':
    response, cursor = None, None
    while True:
        command = ['gh', 'api', 'graphql', '-f', 'query=' + QUERY]
        if cursor:
            command.extend(['-f', 'cursor=' + cursor])
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        page = json.loads(result.stdout)
        if page.get('errors'):
            raise RuntimeError(page['errors'])
        connection = page['data']['user']['repositories']
        if response is None:
            response = page
        else:
            response['data']['user']['repositories']['nodes'].extend(connection['nodes'])
        if not connection['pageInfo']['hasNextPage']:
            break
        cursor = connection['pageInfo']['endCursor']
    generate(response)
