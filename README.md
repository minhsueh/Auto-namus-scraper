# Auto-Namus-Scraper

This repository automatically scrapes data from NamUs (https://namus.nij.ojp.gov/) weekly at midnight on Sunday PST.

**Usage:**
Users can access the data in the `output` folder.
The inner folders are named based on the scraping time, following the format `Year-Month-Day-Hour-Minute-Second`.
Within each inner folder, data is categorized into three types: `MissingPersons`, `UnclaimedPersons`, and `UnidentifiedPersons`.
For each type, JSON files are separated by state. For example, the JSON file for missing persons last sighted in California would be named `MissingPersons_California.json`.

**Note:**
This project is inspired by Prepager's script (https://github.com/Prepager/namus-scraper), with modifications made to collect the full dataset.

**Modifications:**

1. Output Format:

   - The output format has been modified to a dictionary format. This allows users to directly read the data using `json.load()`.
   - The original script generated a list of dictionaries, with each dictionary containing case information returned by API requests.

2. Batch Requests:

   - Requests are now separated into smaller batches. This is done to avoid API restrictions on too many requests, which could result in an incomplete dataset.

3. Automatic Scheduling:
   - Weekly scraping is automated using GitHub Actions. This enables users to perform time-dependent data analysis.

Feel free to contribute or use this repository for your data scraping needs!
