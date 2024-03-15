import os
import json
import grequests
import requests
import functools
import time
import pandas as pd
import datetime

current_time = "{date:%Y-%m-%d-%H-%M-%S}".format(date=datetime.datetime.now())

SEARCH_LIMIT = 10000
REQUEST_BATCH_SIZE = 50
REQUEST_FEEDBACK_INTERVAL = 200

USER_AGENT = "https://github.com/minhsueh"
API_ENDPOINT = "https://www.namus.gov/api"
STATE_ENDPOINT = API_ENDPOINT + "/CaseSets/NamUs/States"
CASE_ENDPOINT = API_ENDPOINT + "/CaseSets/NamUs/{type}/Cases/{case}"
SEARCH_ENDPOINT = API_ENDPOINT + "/CaseSets/NamUs/{type}/Search"

DATA_OUTPUT = "./output/{current_time}/{type}/{type}_{state}.json"
DATA_OUTPUT_PATH = "./output/{current_time}/{type}/"
CASE_TYPES = {
    "MissingPersons": {"stateField": "stateOfLastContact"},
    "UnidentifiedPersons": {"stateField": "stateOfRecovery"},
    "UnclaimedPersons": {"stateField": "stateFound"},
}

completedCases = 0


def main():
    print("Fetching states\n")
    states = requests.get(STATE_ENDPOINT, headers={"User-Agent": USER_AGENT}).json()

    for caseType in CASE_TYPES:
        print("-------------")
        print("Collecting: {type}".format(type=caseType))
        for state in states:
            state_name = state["name"]
            if state_name != "Delaware":
                continue
            print(f"state = {state}")
            output_dict = dict()
            state_list = []
            case_count_list = []

            global completedCases
            completedCases = 0
            failed_count = 0

            print(" > Fetching case identifiers")
            searchRequests = grequests.post(
                SEARCH_ENDPOINT.format(type=caseType),
                headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
                data=json.dumps(
                    {
                        "take": SEARCH_LIMIT,
                        "projections": ["namus2Number"],
                        "predicates": [
                            {
                                "field": CASE_TYPES[caseType]["stateField"],
                                "operator": "IsIn",
                                "values": [state["name"]],
                            }
                        ],
                    }
                ),
            )

            searchRequests = grequests.map([searchRequests], size=REQUEST_BATCH_SIZE)
            cases = functools.reduce(
                lambda output, element: output + element.json()["results"],
                searchRequests,
                [],
            )

            print(" > Found %d cases" % len(cases))

            print(" > Creating output file")
            filePath = DATA_OUTPUT.format(current_time=current_time, type=caseType, state=state_name)
            os.makedirs(os.path.dirname(filePath), exist_ok=True)
            # outputFile = open(filePath, "w")
            # outputFile.write("[")
            print(" > Starting case processing")

            batch_num = (len(cases) // 200) + 1
            for batch_idx in range(batch_num):
                # time.sleep(0.5)
                start_idx = batch_idx * 200
                if batch_idx == batch_num - 1:
                    batch = cases[start_idx:]
                else:
                    end_idx = (batch_idx + 1) * 200
                    batch = cases[start_idx:end_idx]

                caseRequests = (
                    grequests.get(
                        CASE_ENDPOINT.format(type=caseType, case=case["namus2Number"]),
                        hooks={"response": requestFeedback},
                        headers={"User-Agent": USER_AGENT},
                    )
                    for case in batch
                )
                caseRequests = grequests.map(caseRequests, size=REQUEST_BATCH_SIZE)
                for index, case in enumerate(caseRequests):
                    if not case:
                        """
                        print(
                            " > Failed parsing case: {case} index {index}".format(
                                case=cases[index], index=index
                            )
                        )
                        """
                        failed_count += 1
                        continue

                    # outputFile.write(
                    #    case.text + ("," if ((index + 1) != len(caseRequests)) else "")
                    # )
                    tem_output = json.loads(case.text)
                    output_dict[tem_output["id"]] = tem_output
                # print(" > Closing output file")
                # outputFile.write("]")
                # outputFile.close()
            print(" > Completed {count} cases".format(count=completedCases))
            print(f" > failed parsing case count = {failed_count}")
            state_list.append(state_name)
            case_count_list.append(completedCases)
            with open(filePath, "a") as outfile:
                json.dump(output_dict, outfile)
            summary_dict = {"state": state_list, "case_count": case_count_list}
            output_df = pd.DataFrame(summary_dict)
            output_summary_file_name = DATA_OUTPUT_PATH.format(current_time=current_time, type=caseType) + "summary.csv"
            if os.path.exists(output_summary_file_name):
                output_df.to_csv(output_summary_file_name, mode="a", header=False)
            else:
                output_df.to_csv(output_summary_file_name)

    print("Scraping completed")


def requestFeedback(response, **kwargs):
    global completedCases
    completedCases = completedCases + 1

    if completedCases % REQUEST_FEEDBACK_INTERVAL == 0:
        print(" > Completed {count} cases".format(count=completedCases))


main()
