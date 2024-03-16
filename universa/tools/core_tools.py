import os
import json
from typing import List

import requests
from bs4 import BeautifulSoup

from .tool import ToolRegistry
from ..utils.logs import general_logger

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    general_logger.info(
        "dotenv is not installed - loading keys from .env is recommended!"
    )


tool_registry = ToolRegistry()


if "SERP_API_KEY" in os.environ:

    @tool_registry.register_tool
    def web_search(query: str) -> str:
        """
        Perform a web search using the SERP API.

        Args:
            query (str): The search query.

        Returns:
            str: The response from the SERP API.

        Raises:
            KeyError: If the SERP_API_KEY environment variable is not set.
            requests.exceptions.RequestException: If there is an error making the API request.
            json.JSONDecodeError: If there is an error parsing the API response.
        """
        serp_key = os.environ["SERP_API_KEY"]
        url = "https://api.serphouse.com/serp/live"
        payload = json.dumps(
            {
                "data": {
                    "q": query,
                    "domain": "google.com",
                    "loc": "Abernathy,Texas,United States",
                    "lang": "en",
                    "device": "desktop",
                    "serp_type": "web",
                    "page": "1",
                    "verbatim": "0",
                }
            }
        )
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {serp_key}",
        }

        response = requests.request("POST", url, data=payload, headers=headers)
        response_text = json.loads(response.text)
        return response_text


if "GOOGLE_API_KEY" in os.environ:

    @tool_registry.register_tool
    def search_google(query: str, max_result: int = 3) -> List[str]:
        """
        Perform a web search using the Google API.

        Args:
            query (str): The search query.

        Returns:
            str: The response from the Google API.
        """

        google_key = os.environ["GOOGLE_API_KEY"]
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": google_key,
            "cx": os.environ["GOOGLE_CX"],
            "q": query,
        }

        response = requests.get(url, params=params)
        response_text = json.loads(response.text)

        search_results = []

        items = response_text["items"][:max_result]
        for item in items:
            message = {
                "url": item["link"],
                "title": item["title"],
                "snippet": item["snippet"],
            }
            search_results.append(message)

        return search_results


@tool_registry.register_tool
def get_webpage_contents(url: str) -> str:
    """
    Retrieves the contents of a webpage and returns the title and text.

    Args:
        url (str): The URL of the webpage to scrape.

    Returns:
        str: The title and text of the webpage, separated by a newline.
    """
    print(
        f"\n\n--------------------- Executing Web Scrapper Tool -------------------\n\n"
    )
    webpage = requests.get(url).text

    soup = BeautifulSoup(webpage, "lxml")

    text = soup.get_text("")

    if soup.title:
        title = str(soup.title.string)
    else:
        title = ""

    return f"{title}\n\n{text}"


@tool_registry.register_tool
def calculator(expression: str) -> str:
    """It is a simple calculator, which can execute Python expressions: e.g., "(123 + 234) / 23 * 1.5 - 8".

    :param string expression: The python expression you requested.
    :return string: The execution results of the expression.
    """
    globals = {}
    locals = {}
    try:
        print(
            f"\n\n--------------------- Executing Calculator Tool -------------------\n\n"
        )
        # Wrap the code in an eval() call to return the result
        wrapped_code = f"__result__ = eval({repr(expression)}, globals(), locals())"
        exec(wrapped_code, globals, locals)
        return locals.get("__result__", None)
    except Exception as e:
        try:
            # If eval fails, attempt to exec the code without returning a result
            exec(expression, globals, locals)
            return "Code executed successfully."
        except Exception as e:
            return f"Error: {str(e)}"


@tool_registry.register_tool
def get_api_content(url: str, headers: dict, method: str) -> str:
    """
    If provided API specification and the required secret value, return response text.
    Don't analyze the response, just return it.

    Args:
        url (str): The URL of the API to call.
        headers (dict): The header of request API.
        method (str): The method to call the API.

    Returns:
        str: The response from the API.
    """
    print(f"\n\n--------------------- Executing API Call -------------------\n\n")
    print("headers", headers)

    try:
        method = getattr(requests, method.lower())
        response = method(url, headers=headers)
        print("response", response)
        if response.status_code == 200:
            print("response.json", response.json())
            data = response.json()
            return data
        else:
            print(f"Error: {response.status_code}")
            return ""
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        return ""
