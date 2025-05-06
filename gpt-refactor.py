import logging
import os
import time
from typing import List, Dict

import requests
from requests import Session, Response

# Конфигурация
WB_API_TOKEN = os.getenv("WB_API_TOKEN")
WB_WAREHOUSE_ID = os.getenv("WB_WAREHOUSE_ID")
BLOCKED_SKUS = {
    '2037761819099', '2037994608705', '2039385842859', '2039387993436',
    '2039518189264', '2039639220662', '2039690124190', '2039774025344',
    '2039837288853', '2039838180286', '2039843257768', '2039959682690',
    '2039996884194', '2040611809768', '2040634786862', '2041284001022',
    '2041284251243', '2042316671879', '2042478700837', '2042541710497',
    '2042541713290'
}
API_HEADERS = {
    "Authorization": WB_API_TOKEN,
    "Content-Type": "application/json"
}
LOG_LEVEL = logging.INFO
SLEEP_INTERVAL = 600  # 10 минут


# Endpoints
class Endpoints:
    GET_ALL_CARDS = "https://content-api.wildberries.ru/content/v2/get/cards/list"
    WAREHOUSE_STOCKS = f"https://marketplace-api.wildberries.ru/api/v3/stocks/{WB_WAREHOUSE_ID}"


def fetch_all_skus(session: Session, limit: int = 100) -> List[str]:
    """
    Получаем список всех SKU, фильтруя BLOCKED_SKUS.
    """
    payload = {
        "settings": {
            "cursor": {"limit": limit},
            "filter": {"withPhoto": -1}
        }
    }
    response: Response = session.post(Endpoints.GET_ALL_CARDS, json=payload)
    response.raise_for_status()

    cards = response.json().get("cards", [])
    skus = [
        size_data["skus"][0]
        for card in cards
        for size_data in card.get("sizes", [])
        if size_data["skus"][0] not in BLOCKED_SKUS
    ]
    logging.debug(f"Fetched {len(skus)} SKUs (excluded blocked)")
    return skus


def fetch_zero_stock_skus(session: Session, skus: List[str]) -> List[str]:
    """
    Возвращает список SKU, у которых в складе нулевой остаток.
    """
    if not skus:
        return []

    payload = {"skus": skus}
    response: Response = session.post(Endpoints.WAREHOUSE_STOCKS, json=payload)
    response.raise_for_status()

    stocks = response.json().get("stocks", [])
    zero_skus = [item["sku"] for item in stocks if item.get("amount", 0) == 0]
    logging.debug(f"Found {len(zero_skus)} SKUs with zero stock")
    return zero_skus


def replenish_stocks(session: Session, skus: List[str], amount: int = 2) -> None:
    """
    Устанавливает новый остаток `amount` для переданных SKU.
    """
    if not skus:
        logging.info("Нет товаров с 0 в остатках, ничего не делаем.")
        return

    stocks_payload = {"stocks": [{"sku": sku, "amount": amount} for sku in skus]}
    logging.info(f"Обновляем остатки для {len(skus)} SKU: {skus}")

    response: Response = session.put(Endpoints.WAREHOUSE_STOCKS, json=stocks_payload)
    if response.status_code == 204:
        logging.info("Остатки успешно обновлены.")
    else:
        # Логируем тело ответа, если оно есть
        try:
            error_info = response.json()
        except ValueError:
            error_info = response.text
        logging.warning(f"Не удалось обновить остатки (status {response.status_code}): {error_info}")


def main_loop():
    session = requests.Session()
    session.headers.update(API_HEADERS)

    while True:
        try:
            skus = fetch_all_skus(session)
            zero_skus = fetch_zero_stock_skus(session, skus)
            replenish_stocks(session, zero_skus, amount=2)
        except requests.RequestException as e:
            logging.error(f"Ошибка при работе с API: {e}")
        except Exception as e:
            logging.exception(f"Неожиданная ошибка: {e}")

        logging.info(f"Ждем {SLEEP_INTERVAL // 60} минут до следующей итерации...")
        time.sleep(SLEEP_INTERVAL)


if __name__ == "__main__":
    logging.basicConfig(level=LOG_LEVEL,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    main_loop()
