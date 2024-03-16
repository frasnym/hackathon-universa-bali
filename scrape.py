from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def create_driver():
    chrome_options = Options()  # Create ChromeOptions object
    chrome_options.add_argument("--headless")  # Run in headless mode
    driver = webdriver.Chrome(
        options=chrome_options
    )  # Create a new instance of the Chrome driver with headless option
    return driver


# URL of the webpage you want to scrape
url = "https://www.agoda.com/flights/results?cid=-1&departureFrom=DPS&departureFromType=1&arrivalTo=HND&arrivalToType=1&departDate=2024-03-16&returnDate=2024-03-17&searchType=1&cabinType=Economy&adults=1&sort=8"

driver = create_driver()

driver.get(url)

# Wait for the presence of elements with class 'FlightSlice__airline--XfkE0'
wait = WebDriverWait(driver, 10)  # Adjust the timeout as needed
containers = wait.until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".bhCeID"))
)

# Iterate over the containers and extract data
for container in containers:
    # Find elements within the container
    airline_elements = container.find_elements(
        By.CSS_SELECTOR, ".FlightSlice__airline--XfkE0"
    )
    price_elements = container.find_elements(
        By.CSS_SELECTOR, ".iHOveS .FlightPrice__price--d9oH7"
    )

    # Extract data from elements
    for airline_element, price_element in zip(airline_elements, price_elements):
        airline = airline_element.text
        price = price_element.text

        # Do whatever you want with the extracted data
        print("Airline:", airline)
        print("Price:", price)
        print("----")

# Close the WebDriver
driver.quit()
