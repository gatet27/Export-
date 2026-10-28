#!/usr/bin/env python3
"""Export des images secondaires du catalogue public Blue Moon Factory. Python 3.10+."""
import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

SITE = 'https://bluemoonfactory.com'


def fetch(url):
    for attempt in range(4):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'BlueMoonSecondaryImageExporter/1.0', 'Accept': '*/*'})
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read(), response.headers.get_content_type()
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 3:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 3:
                raise
        time.sleep(2 ** (attempt + 1))
    raise RuntimeError('Téléchargement impossible')


def canonical(url):
    parsed = urllib.parse.urlsplit(url)
    return (parsed.netloc.lower(), parsed.path)


def select_secondary(product):
    images = product.get('images', [])
    if not isinstance(images, list):
        raise ValueError('Galerie images invalide')
    images = sorted(images, key=lambda x: int(x.get('position') or images.index(x) + 1))
    if not images:
        return [], None
    # Shopify: la première image de la galerie est la principale.
    # Si une image principale explicite est disponible, on exclut aussi celle-ci.
    primary = images[0]
    explicit = product.get('image') or product.get('featured_image')
    excluded = [primary]
    if isinstance(explicit, dict):
        excluded.append(explicit)
    elif isinstance(explicit, str):
        excluded.append({'src': explicit})
    ids = {str(x['id']) for x in excluded if x.get('id') is not None}
    urls = {canonical(x['src']) for x in excluded if x.get('src')}
    seen = set()
    selected = []
    for image in images:
        src = image.get('src')
        if not src:
            raise ValueError('Image sans URL : export interrompu par prudence')
        key = canonical(src)
        if str(image.get('id')) in ids or key in urls or key in seen:
            continue
        seen.add(key)
        selected.append(image)
    return selected, primary


def catalog():
    products = {}
    page = 1
    while True:
        data, _ = fetch(f'{SITE}/products.json?limit=250&page={page}')
        payload = json.loads(data)
        batch = payload.get('products')
        if not isinstance(batch, list):
            raise ValueError('Le catalogue public a changé : champ products absent')
        if not batch:
            break
        before = len(products)
        for product in batch:
            products[str(product['id'])] = product
        if len(products) == before:
            raise ValueError('La pagination répète la même page ; export incomplet')
        print(f'Page {page} : {len(batch)} produits', flush=True)
        page += 1
        time.sleep(0.4)
    if not products:
        raise ValueError('Aucun produit accessible : aucun export créé')
    return list(products.values())


def export(destination, dry_run=False):
    destination = Path(destination)
    # Évite de mélanger un ancien export avec le nouveau.
    destination.mkdir(parents=True, exist_ok=False)
    products = catalog()
    rows, errors = [], []
    report = {'site': SITE, 'produits': len(products), 'images_secondaires': 0,
              'images_telechargees': 0, 'produits_sans_image_secondaire': 0, 'simulation': dry_run}
    for product in products:
        images, primary = select_secondary(product)
        if not images:
            report['produits_sans_image_secondaire'] += 1
        handle = re.sub(r'[^a-zA-Z0-9_-]', '-', product.get('handle') or 'produit')[:120]
        folder = f"{handle}-{product['id']}"
        for image in images:
            src = image['src']
            extension = Path(urllib.parse.urlsplit(src).path).suffix.lower()
            if extension not in ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif'):
                extension = '.img'
            name = f"images/{folder}/secondaire-{int(image.get('position') or 0):03d}-{image['id']}{extension}"
            row = {'produit_id': product['id'], 'produit': product['title'],
                   'page_produit': f"{SITE}/products/{product['handle']}",
                   'image_principale_exclue': primary['src'], 'image_secondaire': src,
                   'fichier': name, 'statut': 'simulation' if dry_run else 'erreur'}
            report['images_secondaires'] += 1
            if not dry_run:
                try:
                    content, content_type = fetch(src)
                    if not content_type.startswith('image/') or not content:
                        raise ValueError(f'Réponse non image : {content_type}')
                    target = destination / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    temporary = target.with_suffix(target.suffix + '.part')
                    temporary.write_bytes(content)
                    temporary.replace(target)
                    row['statut'] = 'ok'
                    report['images_telechargees'] += 1
                except Exception as exc:
                    errors.append({'url': src, 'erreur': str(exc)})
                time.sleep(0.2)
            rows.append(row)
    fields = ['produit_id', 'produit', 'page_produit', 'image_principale_exclue', 'image_secondaire', 'fichier', 'statut']
    with (destination / 'inventaire.csv').open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    report['erreurs'] = errors
    (destination / 'rapport.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    archive = destination.with_name(destination.name + '.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as output:
        for path in sorted(destination.rglob('*')):
            if path.is_file():
                output.write(path, path.relative_to(destination))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f'Archive : {archive.resolve()}')
    return 1 if errors else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='export-secondaires', help='Nouveau dossier de sortie')
    parser.add_argument('--dry-run', action='store_true', help='Inventaire uniquement, sans télécharger les images')
    args = parser.parse_args()
    try:
        sys.exit(export(args.output, args.dry_run))
    except Exception as exc:
        print(f'Export interrompu : {exc}', file=sys.stderr)
        sys.exit(1)
