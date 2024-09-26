import json
from typing import List, Dict, Any
from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI()


def mock_data() -> List[Dict[str, Any]]:
    return [
        {
            "account_id": "123456",
            "account_central_id": None,
            "account_owner": "John Doe",
        },
        {"account_id": None, "account_central_id": None, "account_owner": "Jane Smith"},
        {
            "account_id": "654321",
            "account_central_id": "CENTRAL_987",
            "account_owner": "Emily Johnson",
        },
        {
            "account_id": None,
            "account_central_id": "CENTRAL_543",
            "account_owner": "Michael Brown",
        },
        {
            "account_id": "345678",
            "account_central_id": None,
            "account_owner": "Olivia Davis",
        },
    ]


def get_account_number(owner: str) -> str:
    # Simulating the tool function
    return f"ACC_{hash(owner) % 1000000:06d}"


def get_central_account_number(account_id: str) -> str:
    # Simulating the tool function
    return f"CENTRAL_{hash(account_id) % 1000000:06d}"


def process_element(element: Dict[str, Any]) -> Dict[str, Any]:
    system_message = """
    You are an AI assistant that helps process account information.
    Your task is to examine the given JSON object and determine if any fields are missing.
    You should suggest actions to fill in missing fields in the correct order.
    Provide your response as a list of JSON objects, each with 'action' and 'input' fields.
    """

    user_message = f"""
    Examine the following JSON object and determine what actions to take:
    {json.dumps(element)}

    If account_id is missing, include this action:
    {{"action": "get_account_number", "input": "<owner_name>"}}

    If account_central_id is missing, include this action:
    {{"action": "get_central_account_number", "input": "<account_id>"}}

    If both fields are present or no action is needed, respond with:
    [{{"action": "none", "input": null}}]

    Ensure that if both actions are needed, get_account_number comes before get_central_account_number.
    Provide your response as a list of JSON objects.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
    )

    actions = json.loads(response.choices[0].message.content)

    for action in actions:
        if action["action"] == "get_account_number":
            element["account_id"] = get_account_number(action["input"])
        elif action["action"] == "get_central_account_number":
            if element["account_id"] is None:
                print(
                    f"Warning: Attempted to get central account number for {element['account_owner']} without an account_id."
                )
                continue
            element["account_central_id"] = get_central_account_number(
                element["account_id"]
            )

    return element


def fill_missing_properties():
    updated_data = []

    for element in mock_data():
        print(f"Processing element: {element}")
        updated_element = process_element(element)
        updated_data.append(updated_element)

    # Save the updated data to a new JSON file
    with open("filled_data.json", "w") as json_file:
        json.dump(updated_data, json_file, indent=4)

    print("Updated JSON file has been saved as 'filled_data.json'.")


if __name__ == "__main__":
    fill_missing_properties()
