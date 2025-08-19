import requests

def search_yacy(query, limit=5):
    try:
        url = f"http://localhost:8090/yacysearch.json"
        params = {
            "query": query,
            "maximumRecords": limit
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        channels = data.get('channels', [])
        items = channels[0].get('items', []) if channels else []

        results = []
        for item in items:
            results.append({
                'title': item.get('title', 'No Title'),
                'link': item.get('link', '#'),
                'description': item.get('description', '')
            })

        return results

    except Exception as e:
        return [{'error': f"YaCy error: {str(e)}"}]
