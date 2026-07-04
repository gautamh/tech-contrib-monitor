"""
This script fetches campaign finance data from the FEC API.

It retrieves two types of data:
1. Individual contributions from a predefined list of tech executives (Schedule A).
2. Expenditures by a predefined list of corporate PACs (Schedule B).

The raw data is saved to JSON files in the `static/data` directory for further processing.
"""

import os
import json
import time
from typing import List, Dict
from dataclasses import dataclass

import requests
from dotenv import load_dotenv

# --- Configuration ---

BASE_URL = "https://api.open.fec.gov/v1/"

# A list of corporate PACs to track.
# The keys are for reference; the script uses the committee IDs.
PAC_IDS = {
    "Google": "C00428623",
    "Meta": "C00502906",
    "Microsoft": "C00227546"
}

# --- Dataclasses ---

@dataclass
class Contributor:
    """Represents a political contributor to search for."""
    name: str
    employer: str

# A list of tech executives to track.
CONTRIBUTORS_TO_TRACK = [
    Contributor(
        name="Sundar Pichai",
        employer="Google"),
    Contributor(
        name="Kent Walker",
        employer="Google"),
    Contributor(
        name="Thomas Kurian",
        employer="Google"),
    Contributor(
        name="Jen Fitzpatrick",
        employer="Google"),
    Contributor(
        name="Rick Osterloh",
        employer="Google"),
    Contributor(
        name="Prabhakar Raghavan",
        employer="Google"),
    Contributor(
        name="Lorraine Twohill",
        employer="Google"),
    Contributor(
        name="Corey DuBrowa",
        employer="Google"),
    Contributor(
        name="Neal Mohan",
        employer="Google"),
    Contributor(
        name="Anat Ashkenazi",
        employer="Google"),
    Contributor(
        name="Jeff Dean",
        employer="Google"),
    Contributor(
        name="Ruth Porat",
        employer="Google"),
    Contributor(name="Mark Zuckerberg", employer="Meta"), # Founder, Chairman & CEO
    Contributor(name="Janelle Gale", employer="Meta"), # VP, HR
    Contributor(name="Joel Kaplan", employer="Meta"), # President, Global Affairs
    Contributor(name="Ahmad Al-Dahle", employer="Meta"), # VP & Head of GenAI
    Contributor(name="Javier Olivan", employer="Meta"), # COO
    Contributor(name="Susan Li", employer="Meta"), # CFO
    Contributor(name="David Wehner", employer="Meta"), # Chief Strategy Officer
    Contributor(name="Jennifer Newstead", employer="Meta"), # Chief Legal Officer
    Contributor(name="Chris Cox", employer="Meta"), # CPO
    Contributor(name="Andrew Bosworth", employer="Meta"), # CTO
    Contributor(name="MIKE SCHROEPFER", employer="Meta"), # Senior Fellow
    Contributor(name="Satya Nadella", employer="Microsoft"), # Chairman & CEO
    Contributor(name="Jon Palmer", employer="Microsoft"), # Chief Legal Officer
    Contributor(name="Maitha Alsuwaidi", employer="Microsoft"), # Chief Strategy & Business Officer
    Contributor(name="Asfar Rizvi", employer="Microsoft"), # Executive Leadership Committee - Nominated Member
    Contributor(name="Amy Coleman", employer="Microsoft"), # Chief People Officer
    Contributor(name="Carolina Dybeck Happe", employer="Microsoft"), # COO
    Contributor(name="Mustafa Suleyman", employer="Microsoft"), # CEO, Microsoft AI
    Contributor(name="Samer Abu-Ltaif", employer="Microsoft"), # President, Microsoft CEMA
    Contributor(name="Amy Hood", employer="Microsoft"), # EVP & CFO
    Contributor(name="Judson Althoff", employer="Microsoft"), # CEO, Microsoft Commercial Business
    Contributor(name="Brad Smith", employer="Microsoft"), # President & Vice Chair
    Contributor(name="Charlie Bell", employer="Microsoft"), # EVP, Security, Compliance, Identity & Management
    Contributor(name="Kevin Scott", employer="Microsoft"), # CTO & EVP, Technology
]

# --- API Fetching Class ---

class FECContributionAnalyzer:
    """A client to fetch data from the FEC API with built-in retry logic."""
    def __init__(self, api_key: str):
        """Initializes the analyzer with an FEC API key."""
        self.api_key = api_key
        self.base_params = {
            'api_key': api_key,
            'sort_hide_null': False,
            'sort_nulls_last': False,
            'per_page': 100,
        }

    def _fetch_paginated_data(self, endpoint: str, params: Dict, description: str) -> List[Dict]:
        """Generic helper to fetch all pages for a given FEC endpoint.

        Args:
            endpoint: The specific API endpoint URL.
            params: The query parameters for the request.
            description: A description of the data being fetched, for logging.

        Returns:
            A list of all result dictionaries from all pages.
        """
        all_results = []
        page = 1
        retries = 3

        while True:
            params['page'] = page
            response = None

            for attempt in range(retries):
                try:
                    print(f"Fetching {description} (page {page}), attempt {attempt + 1}")
                    response = requests.get(endpoint, params=params, timeout=30)
                    if response.status_code == 200:
                        break  # Success
                    else:
                        print(f"API request failed, status: {response.status_code}. Retrying in 5s...")
                        time.sleep(5)
                except requests.exceptions.RequestException as e:
                    print(f"API request exception: {e}. Retrying in 5s...")
                    time.sleep(5)
            
            if response is None or response.status_code != 200:
                print(f"All retries failed for {description} (page {page}). Skipping.")
                break

            data = response.json()
            results = data.get('results', [])
            if not results:
                break
                
            all_results.extend(results)
            
            if 'pagination' not in data or page >= data['pagination']['pages']:
                break
            page += 1
        
        return all_results

    def get_contributor_data(self, contributor: Contributor, start_date: str, end_date: str) -> List[Dict]:
        """Fetches all Schedule A contributions for a given individual.
        
        Args:
            contributor: The individual to search for.
            start_date: The start of the date range (MM/DD/YYYY).
            end_date: The end of the date range (MM/DD/YYYY).

        Returns:
            A list of raw contribution records.
        """
        params = self.base_params.copy()
        params.update({
            'contributor_name': contributor.name,
            'contributor_employer': contributor.employer,
            'min_date': start_date,
            'max_date': end_date,
            'sort': '-contribution_receipt_date',
            'is_individual': True,
        })
        endpoint = f"{BASE_URL}schedules/schedule_a/"
        description = f"individual contributions for {contributor.name}"
        return self._fetch_paginated_data(endpoint, params, description)

    def get_pac_expenditures(self, pac_ids: List[str], start_date: str, end_date: str) -> List[Dict]:
        """Fetches all Schedule B expenditures for a given list of PACs.

        Args:
            pac_ids: A list of committee IDs for the PACs to query.
            start_date: The start of the date range (MM/DD/YYYY).
            end_date: The end of the date range (MM/DD/YYYY).

        Returns:
            A list of raw expenditure records.
        """
        all_expenditures = []
        endpoint = f"{BASE_URL}schedules/schedule_b/"
        
        for pac_id in pac_ids:
            params = self.base_params.copy()
            params.update({
                'committee_id': pac_id,
                'min_date': start_date,
                'max_date': end_date,
                'sort': '-disbursement_date',
            })
            description = f"PAC expenditures for {pac_id}"
            all_expenditures.extend(self._fetch_paginated_data(endpoint, params, description))
        
        return all_expenditures

# --- Main Execution ---

def main():
    """Main function to fetch all data and save it to raw JSON files."""
    load_dotenv()

    api_key = os.getenv('FEC_API_KEY')
    if not api_key:
        raise ValueError("FEC_API_KEY environment variable not set. Please create a .env file.")
        
    analyzer = FECContributionAnalyzer(api_key)
    # Fetch contributions from 2023 through 2028 (next couple of years)
    start_date="01/01/2023"
    end_date="12/31/2028"
    
    # --- Fetch and save individual contributions ---
    output_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'data', 'contributions.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Load existing contributions
    existing_contributions = {}
    if os.path.exists(output_path):
        with open(output_path, 'r') as f:
            try:
                data = json.load(f)
                for item in data:
                    existing_contributions[item['transaction_id']] = item
            except json.JSONDecodeError:
                print("Could not decode existing contributions file. Starting fresh.")

    # Fetch new contributions
    for contributor in CONTRIBUTORS_TO_TRACK:
        contributions = analyzer.get_contributor_data(contributor, start_date, end_date)
        for contribution in contributions:
            existing_contributions[contribution['transaction_id']] = contribution
    
    deduplicated_contributions = list(existing_contributions.values())

    with open(output_path, 'w') as f:
        json.dump(deduplicated_contributions, f, indent=2)
    print(f"Successfully wrote {len(deduplicated_contributions)} individual contributions to {output_path}")

    # --- Fetch and save PAC expenditures ---
    pac_expenditures = analyzer.get_pac_expenditures(list(PAC_IDS.values()), start_date, end_date)
    pac_output_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'data', 'pac_contributions.json')
    with open(pac_output_path, 'w') as f:
        json.dump(pac_expenditures, f, indent=2)
    print(f"Successfully wrote {len(pac_expenditures)} PAC expenditures to {pac_output_path}")

if __name__ == "__main__":
    main()
