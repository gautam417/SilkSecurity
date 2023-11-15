# Host Deduplication Pipeline

This Python script is designed to interact with third party vendors such as Qualys and Crowdstrike and using their APIs for the purpose of fetching host data, normalizing it, deduplicating entries, and generating meaningful visualizations to provide insights into the distribution of operating systems and hardware manufacturers of the scanned hosts.

## Requirements

- Python 3.10
- MongoDB server (local or remote)
- Python packages: `requests`, `matplotlib`, `seaborn`, `pymongo`

## Setup

1. Ensure that MongoDB is installed and running on your local system or accessible remotely.
   
2. Clone the repository to your local machine.

3. Install the required Python packages by running the following command:

   ```bash
   pip install -r requirements.txt

## Usage

To run the script, use the following command in your terminal:

   ```bash
   python silk_security.py
   ```
The script will connect to the configured MongoDB instance, fetch data from Qualys and Crowdstrike, perform deduplication, and save the deduplicated data into the database.

## Visualizations

The script generates two bar charts: one showing the distribution of operating systems, and another showing the hardware manufacturer distribution. These charts will be saved locally and can be used for reports and analytics purposes for scanned hosts data.

## Configuration

Before running the script, make sure to configure the following:

- MongoDB connection string in the script to point to the MongoDB server.
- API keys and access configurations for Qualys and Crowdstrike.
