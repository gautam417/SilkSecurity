import requests
import logging
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from pymongo import MongoClient

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API Configuration
API_TOKEN = 'gautam417@yahoo.com_b8f71e44-f5dd-48b9-ace7-9eb3a6dc148b'
QUALYS_URL = 'https://api.recruiting.app.silk.security/api/qualys/hosts/get'
CROWDSTRIKE_URL = 'https://api.recruiting.app.silk.security/api/crowdstrike/hosts/get'

# MongoDB Configuration
mongo_client = MongoClient('localhost', 27017)
db = mongo_client['host_data']
raw_qualys_collection = db['raw_qualys']
raw_crowdstrike_collection = db['raw_crowdstrike']
normalized_collection = db['normalized_hosts']
deduped_collection = db['deduped_hosts']


def fetch_data(api_url, api_token, skip=0, limit=2):
    headers = {
        'token': api_token,
        'accept': 'application/json'
    }
    payload = {'skip': skip, 'limit': limit}
    try:
        response = requests.post(api_url, headers=headers, params=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data: {e}")
        return None

def insert_raw_to_mongo(collection, data):
    try:
        collection.insert_many(data)
        logging.info(f"Inserted {len(data)} raw documents into {collection.name} collection.")
    except Exception as e:
        logging.error(f"Error inserting raw data into MongoDB: {e}")

# Normalization Aggregation Pipeline
normalization_pipeline = [
    {
        '$addFields': {
            'hostname': {
                '$cond': {
                    'if': {'$ifNull': ['$dnsHostName', False]},
                    'then': '$dnsHostName',
                    'else': '$hostname'
                }
            },
            'ip_address': {
                '$cond': {
                    'if': {'$ifNull': ['$external_ip', False]},
                    'then': '$external_ip',
                    'else': '$address'
                }
            },
            'operating_system': {
                '$cond': {
                    'if': {'$ifNull': ['$os_version', False]},
                    'then': '$os_version',
                    'else': {
                        '$concat': [
                            {'$ifNull': ['$os.name', '']},
                            ' ',
                            {'$ifNull': ['$os.version', '']}
                        ]
                    }
                }
            },
            'manufacturer': {
                '$cond': {
                    'if': {'$ifNull': ['$system_manufacturer', False]},
                    'then': '$system_manufacturer',
                    'else': '$manufacturer'
                }
            },
            'model': {
                '$cond': {
                    'if': {'$ifNull': ['$system_product_name', False]},
                    'then': '$system_product_name',
                    'else': '$model'
                }
            }
        }
    },
    {'$merge': 'normalized_hosts'}
]

# Deduplication Aggregation Pipeline
deduplication_pipeline = [
    {
        '$group': {
            '_id': {
                'hostname': '$hostname', 
                'ip_address': '$ip_address'
            },
            'host_documents': {'$push': '$$ROOT'}
        }
    },
    {
        '$replaceRoot': {
            'newRoot': {
                '$mergeObjects': [
                    {'$arrayElemAt': ['$host_documents', 0]}, 
                    {'unique_ids': '$host_documents._id'},
                    {'host_documents': '$$REMOVE'}
                ]
            }
        }
    },
    {'$merge': 'deduped_hosts'}
]

def prepare_visualization_data(deduped_data):
    os_counts = defaultdict(int)
    manufacturer_counts = defaultdict(int)
    
    for host in deduped_data:
        # Counting operating systems
        os = (host.get('operating_system') or 'Unknown').strip()
        os_counts[os if os else 'Unknown'] += 1


        # Counting hardware manufacturers
        manufacturer = host.get('manufacturer', 'Unknown')
        manufacturer_counts[manufacturer] += 1

    # Print out the operating systems and their counts
    for os, count in os_counts.items():
        print(f"Operating System: {os}, Count: {count}")

    return os_counts, manufacturer_counts


def create_visualizations(os_counts, manufacturer_counts):
    fig, axs = plt.subplots(2, 1, figsize=(10, 10))

    # Operating System Distribution
    os_names, os_values = zip(*os_counts.items())
    sns.barplot(x=list(os_names), y=list(os_values), ax=axs[0])
    axs[0].set_title('Operating System Distribution')
    axs[0].set_xlabel('Operating System')
    axs[0].set_ylabel('Count')

    # Hardware Manufacturer Distribution
    manufacturer_names, manufacturer_values = zip(*manufacturer_counts.items())
    sns.barplot(x=list(manufacturer_names), y=list(manufacturer_values), ax=axs[1])
    axs[1].set_title('Hardware Manufacturer Distribution')
    axs[1].set_xlabel('Manufacturer')
    axs[1].set_ylabel('Count')

    plt.tight_layout()
    plt.savefig('deduped_hosts_visualization.png')
    logging.info("Visualization saved as 'deduped_hosts_visualization.png'.")

def main():
    qualys_data = fetch_data(QUALYS_URL, API_TOKEN, skip=0, limit=2)
    crowdstrike_data = fetch_data(CROWDSTRIKE_URL, API_TOKEN, skip=0, limit=2)
    
    if qualys_data and crowdstrike_data:
        insert_raw_to_mongo(raw_qualys_collection, qualys_data)
        insert_raw_to_mongo(raw_crowdstrike_collection, crowdstrike_data)

        raw_qualys_collection.aggregate(normalization_pipeline)
        raw_crowdstrike_collection.aggregate(normalization_pipeline)
        normalized_collection.aggregate(deduplication_pipeline)
        
        deduped_data = list(deduped_collection.find())
        os_counts, manufacturer_counts = prepare_visualization_data(deduped_data)
        create_visualizations(os_counts, manufacturer_counts)
    else:
        logging.error("Failed to fetch data.")

if __name__ == "__main__":
    main()

