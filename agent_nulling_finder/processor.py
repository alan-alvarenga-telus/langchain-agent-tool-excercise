from langchain.tools import tool


@tool
def get_account_number(account_owner: str) -> str:
    """Returns the account number id based on the name of the account owner"""
    return f"{account_owner}-999"


@tool
def get_central_account_number(account_id: str) -> str:
    """
    Returns the central account number id based on the account number id
    """
    return f"{account_id}-central-account"
