import requests
from . import utils

class Here:
    def __init__(self, here_url, here_api_key):
        self.here_url = here_url
        self.here_api_key = here_api_key

    def _location(self, params):
        params = params.copy()
        params["apiKey"] = self.here_api_key

        location = requests.get(
            'https://geocode.search.hereapi.com/v1/geocode',
            params)

        results = []

        for v in location.json()["items"]:
          try:
            city = v['address']['city']
            state = v["address"]["stateCode"]
            location = f"{city}, {state}"
          except:
            location = v['title']

          results.append([location, v["position"]['lat'], v["position"]['lng']])

        return results
     
  
    def get_location_by_zip(self, zipcode, country):
        """
        Get location by zip and country
        """
    
        results = self._location(
            params={
                'qq': f"postalCode={zipcode};country={country}"
            }
        )

        if len(results) == 1:
            return results[0]
        else:
            raise Exception(f"Unable to find a proper match for {zipcode}")

    def search_location(self, text):
        """
        Search for a location
        """
    
        results = self._location(
            params={
                "q": text
            }
        )

        if len(results) == 1:
            return results[0]
        elif len(results) == 0:
            raise Exception(f"Unable to find any matchs for {text}")
        else:
            matches = ' | '.join([x[0] for x in results])
            raise Exception(f"Unable to find a proper match for {text}: {matches}")

    def location(self, text):
        country = utils.postal_code(text)
        if country:
            return self.get_location_by_zip(text, country)
        else:
            return self.search_location(text)

