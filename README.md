# Tool Calling

Assistant en ligne de commande qui répond à une question en laissant un LLM
(via OpenRouter) appeler des outils Python : l'heure locale et la météo d'une ville.
Ce projet sert de socle propre : architecture en couches, tests sans appel payant,
gestion des erreurs, retries et logs structurés.

## Installation

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuration

Copier `.env.example` vers `.env`, puis renseigner :

- `OPENROUTER_API_KEY` : clé créée depuis un compte OpenRouter (openrouter.ai) ;
- `METEO_API_KEY` : clé gratuite créée depuis un compte WeatherAPI (weatherapi.com).

Les autres variables sont facultatives. Leurs valeurs par défaut sont définies
dans `src/config.py` (modèle, `max_tokens`, `max_retries`, `base_delay`).

## Utilisation

```powershell
py -m src.main
```

Les logs JSON sont affichés dans la console et écrits dans `log/app.log`.
Chaque question reçoit un `request_id` commun à tous ses logs.

## Tests et qualité

```powershell
py -m pytest -v
ruff check .
```

Les tests n'effectuent aucun appel réseau ni appel LLM payant : le provider,
les outils et la fonction d'attente sont remplacés par des doublures.

## Architecture

| Élément | Rôle |
|---|---|
| `src/domain/` | Vocabulaire commun : contrat du provider (`Protocol`) et exceptions `LLMTransientError` / `LLMFatalError` |
| `src/providers/` | Communication avec OpenRouter : requête HTTP, traduction des erreurs, retries, validation de la réponse |
| `src/services/` | Orchestration : boucle LLM → outils → LLM, plafonnée par `max_steps` |
| `src/tools/` | Outils, registre (nom → fonction), descriptions envoyées au LLM, exécution protégée |
| `src/utils/` | Logger JSON et `request_id` |
| `src/config.py` | Configuration typée et validée (`pydantic-settings`) |
| `src/main.py` | Point d'entrée : charge la configuration, assemble les composants, affiche le résultat |

Trajet d'une question :
`main.py` → service → provider (LLM) → service → registre → outil → service → provider → réponse finale.

## Choix techniques

**Injection des dépendances.** Le service reçoit son provider et son registre ;
le provider reçoit sa fonction d'attente ; l'outil météo reçoit sa clé.
Chaque dépendance lente, payante ou imprévisible peut ainsi être remplacée dans
les tests, sans modifier le code testé.

**Erreurs transitoires et fatales.** Critère : la même requête peut-elle réussir
plus tard ? Timeout, réseau, 429 et 5xx sont transitoires et déclenchent jusqu'à
`max_retries` essais, avec une attente croissante (1 s, 2 s…). Les autres erreurs
HTTP et les réponses illisibles ou mal structurées sont fatales : réessayer
coûterait un appel sans résultat probable.

**Séparation essai / politique d'essais.** `_raw_llm` réalise un appel et traduit
ses erreurs ; `call_llm` décide du nombre d'essais et des attentes. Changer de
fournisseur ou de politique de retry ne modifie qu'une seule méthode.

**Validation à la frontière.** La structure des `tool_calls` (`id`, `function`,
`name`) est vérifiée dans le provider, là où les données entrent dans le programme.
Le service et le registre peuvent ensuite les utiliser sans vérification.

**Outils qui ne font jamais planter la conversation.** `execute_tool` attrape
volontairement toutes les exceptions (`noqa: BLE001`) : un outil inconnu,
des arguments invalides ou un outil en échec deviennent un message d'erreur
transmis au LLM, qui peut corriger sa demande.

**Logs sans données sensibles.** Les logs contiennent des événements nommés,
des mesures (latence, tokens, durée d'outil) et le type d'erreur
(`type(e).__name__`), jamais `str(e)`, les headers, les questions ni les
arguments des outils : ces textes peuvent contenir une clé API ou des données
personnelles.

## Limites connues

- Le provider renvoie un dictionnaire au format OpenAI : le service dépend de ce format.
- Le modèle ne choisit pas toujours d'appeler un outil : il répond parfois sans l'utiliser.
- Au dernier tour autorisé, les outils demandés sont exécutés, mais leur résultat
  n'est pas renvoyé au LLM. Acceptable pour des outils de lecture, à revoir pour
  des outils qui modifient des données.
- `get_current_time` renvoie l'heure de la machine qui exécute le programme,
  pas celle de l'utilisateur.