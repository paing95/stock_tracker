import traceback
from datetime import datetime

import bs4
import log_helper

from django.core.management.base import BaseCommand
from django.conf import settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from stock import models

logger = log_helper.getLogger("Sync Companies")

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            logger.debug('Syncing S&P 500 Companies')
            # clean up all records
            models.Company.objects.all().delete()

            driver = webdriver.Chrome()
            driver.get(settings.COMPANY_RETRIEVAL_URL)
            
            row_locator = (By.CSS_SELECTOR, '#constituents tr')
            WebDriverWait(driver, 30).until(
                EC.presence_of_all_elements_located(row_locator)
            )
            table_rows_raw = driver.find_elements(*row_locator)
            
            objects = []
            for trr in table_rows_raw:
                soup = bs4.BeautifulSoup(trr.get_attribute('outerHTML'), 'html.parser')
                columns = soup.find_all('td')
                if not columns: continue

                columns = [col.text.strip() for col in columns]
                obj = models.Company()
                obj.ticker = columns[0]
                obj.name = columns[1]
                obj.sector = columns[2]
                obj.industry = columns[3]
                obj.location = columns[4]
                obj.entry_date = datetime.strptime(columns[5], "%Y-%m-%d")
                obj.cik_key = columns[6]
                obj.founded_year = datetime.now().replace(day=1, month=1, year=int(columns[7][:4]))
                objects.append(obj)
            
            # bulk create
            models.Company.objects.bulk_create(objects)
            # clean up
            driver.quit()
            logger.debug("Finished Syncing...")
        except Exception as e:
            logger.error("Error syncing companies: {}".format(e))
            logger.error(traceback.format_exc())