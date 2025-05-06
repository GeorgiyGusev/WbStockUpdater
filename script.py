import logging

import requests
import time


token = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwNDE3djEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc2MjI0NTEwMiwiaWQiOiIwMTk2YTIyNS1iNTAzLTc0NjgtYjUwYS03NjRiYjYzMjQ4MDgiLCJpaWQiOjIyMDA0MTAyLCJvaWQiOjEyNzE2NTYsInMiOjE4LCJzaWQiOiI4YWViMGFlMC02YmVmLTQ0OGEtOTFhYy1hMTcxYjc0NzU5ZDkiLCJ0IjpmYWxzZSwidWlkIjoyMjAwNDEwMn0.Ukt23ZmiKPDjTxB3QJr5cM78cpYVq967n32UsSUc61W7oIoJ0jD4AYMOy7K81G3SViHIuof2lmml34Cfzq0esg"
headers = {
    "Authorization": f"{token}",
    "Content-Type": "application/json"
}

blocked_skus = ['2037761819099', '2037994608705', '2039385842859', '2039387993436', '2039518189264', '2039639220662',
                '2039690124190', '2039774025344', '2039837288853', '2039838180286', '2039843257768', '2039959682690',
                '2039996884194', '2040611809768', '2040634786862', '2041284001022', '2041284251243', '2042316671879',
                '2042478700837', '2042541710497', '2042541713290']


class Endpoints:
    GetAllCards = "https://content-api.wildberries.ru/content/v2/get/cards/list"
    SmolenskWarehouseStocks = "https://marketplace-api.wildberries.ru/api/v3/stocks/736243"


def main():
    get_all_items_body = {
        "settings": {
            "cursor": {
                "limit": 100
            },
            "filter": {
                "withPhoto": -1
            }
        }
    }
    # получение всех товаров и записывание их баркодов
    req = requests.post(url=Endpoints.GetAllCards, headers=headers, json=get_all_items_body)
    all_items = req.json()
    skus = []
    for item in all_items["cards"]:
        for size in item["sizes"]:
            if size["skus"][0] in blocked_skus:
                continue
            skus.append(size["skus"][0])

    get_all_stocks_body = {
        "skus": skus,
    }

    skus_with_zero_stock = []
    stocks = requests.post(url=Endpoints.SmolenskWarehouseStocks, headers=headers, json=get_all_stocks_body).json()
    for stock in stocks["stocks"]:
        if stock["amount"] == 0:
            skus_with_zero_stock.append(stock["sku"])
    new_stocks = []
    for zero_sku in skus_with_zero_stock:
        new_stocks.append(
            {
                "sku": zero_sku,
                "amount": 2
            }
        )
    update_stocks_body = {
        "stocks": new_stocks
    }
    if len(new_stocks) <= 0:
        logging.warning("Нет товаров с 0 в остатках, пропускаем круг")
        return
    logging.info(f"Устанавливаем остатки для баркодов. Новые остатки: {new_stocks}")
    res = requests.put(url=Endpoints.SmolenskWarehouseStocks, headers=headers, json=update_stocks_body)
    if res.status_code != 204:
        logging.warning('Остатки не обновлены, ответ сервера:', res.json(), "статус код:", res.status_code)
        return
    logging.info("Остатки успещно обновлены")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    while True:
        main()
        logging.info("Ожидание 10 минут...")
        time.sleep(600)  # 600 секунд = 10 минуyfgт
