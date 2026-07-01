import concurrent.futures
from mcp.server.fastmcp import FastMCP
from youtubesearchpython import VideosSearch

mcp = FastMCP("YouTube_Tutor")

def _convertir_en_secondes(duree_str):
    if not duree_str:
        return 999999
    parties = duree_str.split(':')
    try:
        if len(parties) == 2:
            return int(parties[0]) * 60 + int(parties[1])
        elif len(parties) == 3:
            return int(parties[0]) * 3600 + int(parties[1]) * 60 + int(parties[2])
    except ValueError:
        pass
    return 999999

@mcp.tool()
def search_best_youtube_video(sujet: str, duree_max_minutes: int = 10, result_limit: int = 30, timeout_seconds: float = 5.0) -> str:
    """
    Search on YouTube and return the best educational video link.
    Filters long videos, scans more results to increase relevance, and returns a default if no result comes quickly.
    """
    try:
        recherche = VideosSearch(sujet, limit=result_limit)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(recherche.result)
            try:
                result_data = future.result(timeout=timeout_seconds)
            except concurrent.futures.TimeoutError:
                return "DEFAULT: Recherche trop longue, aucune vidéo trouvée rapidement."

        resultats = result_data.get('result', [])
        
        if not resultats:
            return "DEFAULT: Aucune vidéo trouvée rapidement pour ce sujet."
            
        max_seconds = duree_max_minutes * 60
        meilleur_court = None
        meilleur_secours = None
        meilleure_duree = None

        for video in resultats:
            duree_texte = video.get('duration')
            secondes = _convertir_en_secondes(duree_texte)

            if secondes <= max_seconds:
                meilleur_court = video
                break

            if meilleure_duree is None or secondes < meilleure_duree:
                meilleure_duree = secondes
                meilleur_secours = video
            
        if meilleur_court:
            video_choisie = meilleur_court
            tag = "Lien trouvé"
        else:
            video_choisie = meilleur_secours or resultats[0]
            tag = "Lien de secours trouvé"

        titre = video_choisie.get('title')
        lien = video_choisie.get('link')
        chaine = video_choisie.get('channel', {}).get('name', 'Inconnu')
        return f"{tag} ! Titre: {titre} (Chaîne: {chaine}). URL: {lien}"
        
    except Exception as e:
        return f"ERROR: Technical issue during search: {str(e)}"

if __name__ == "__main__":
    mcp.run()