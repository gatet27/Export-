# Blue Moon Factory — images secondaires uniquement

Outil Python sans dépendance pour exporter les images secondaires de **tous les produits publics** de https://bluemoonfactory.com.

## Utiliser depuis GitHub (sans installer Python)

1. Créer un dépôt GitHub et y déposer le **contenu** de cette archive, pas le ZIP lui-même.
2. Vérifier que `export_images.py` et `README.md` sont à la racine et que le fichier du workflow est à `.github/workflows/export.yml`. Le dossier `.github` peut être masqué sur votre ordinateur : il doit être inclus.
3. Ouvrir l’onglet **Actions**, activer les workflows si GitHub le demande, puis choisir **Exporter les images secondaires**.
4. Cliquer sur **Run workflow**, puis confirmer **Run workflow**.
5. À la fin, ouvrir l’exécution et télécharger **bluemoon-images-secondaires** dans **Artifacts**. Décompresser le téléchargement, puis `export-secondaires.zip`.

GitHub Actions exécute le téléchargement côté serveur : GitHub Pages n’est pas nécessaire. Les artefacts sont conservés 7 jours. L’outil ne publie pas les photos dans le dépôt.

## Contenu de l’export

- `images/` : un dossier par produit, seulement ses photos secondaires en résolution fournie par le catalogue, sans réduction ajoutée.
- `inventaire.csv` : produit, lien de sa fiche, URL principale exclue, URL secondaire, fichier et résultat.
- `rapport.json` : nombre de produits, images, produits sans photo secondaire et erreurs éventuelles.

**Règle précise :** la première image de la galerie Shopify (position la plus basse) est exclue. Si le catalogue fournit aussi un champ d’image principale explicite, celle-ci est exclue également. Une copie de la même URL principale avec une autre query string est aussi exclue. La comparaison est faite par identifiant et URL, sans reconnaissance visuelle : une photo identique réimportée sous un nouvel identifiant et une autre URL n’est pas détectée.

Les photos de variantes présentes après l’image principale sont considérées comme secondaires. Les produits sans image secondaire ne génèrent aucune photo. Les vidéos, logos, bannières et images des descriptions ne sont pas exportés. Une photo secondaire d’un produit reste exportable même si elle est principale sur un autre produit.

Le nombre de produits n’est pas fixé à 177 : toutes les pages sont parcourues jusqu’à une page vide, y compris si le catalogue dépasse 250 produits. Seuls les produits publiquement accessibles sont disponibles ; les brouillons et produits privés ne le sont pas. Un changement de catalogue pendant l’exécution peut modifier le résultat.

## Utiliser en local

Python 3.10 ou ultérieur :

```bash
python export_images.py
```

Créer seulement l’inventaire :

```bash
python export_images.py --dry-run --output verification
```

Pour relancer, choisir un nouveau dossier (`--output export-2`) ou déplacer l’ancien. Le programme refuse un dossier existant pour éviter de mélanger plusieurs exports. Les requêtes sont séquentielles, avec pauses et nouvelles tentatives sur erreurs temporaires. En cas de téléchargement partiel, l’archive et le rapport restent disponibles mais l’exécution est signalée en échec. En cas d’erreur de catalogue, aucun export complet n’est annoncé.

Tests : `python -m unittest -v`.

Les droits sur les images restent ceux de leurs titulaires. Leur téléchargement ne transfère aucun droit de republication.
