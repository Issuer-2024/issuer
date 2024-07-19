import requests


class RequestSuggestions:

    @staticmethod
    def get_suggestions(query):
        suggestions_api_url = f"http://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={query}&hl=ko"
        suggestions_response = requests.get(suggestions_api_url)
        return suggestions_response.json()[1]
