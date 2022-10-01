import os
import logging
import requests

from bs4 import BeautifulSoup


def get_web_page(url, header):
    resp = requests.get(url, headers=header)

    # check response encodeing
    if resp.encoding == "ISO-8859-1":
        resp.encoding = "utf-8"

    if resp.status_code != 200:
        raise RuntimeError(f"Invalid URL {resp.url} {resp.status_code}")
    return resp


def line_notify(line_token, msg):
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {line_token}"}
    payload = {"message": msg}
    r = requests.post(url, headers=headers, params=payload)
    line_status = r.status_code
    logging.debug("Line notify status code [%s]", line_status)
    return line_status


def encode_iso8859_to_utf8(text):
    try:
        encode_text = text.strip().encode(
            "iso-8859-1").decode("utf-8", errors="replace")
        return encode_text
    except Exception:
        return text.strip()


def get_foreign_currency(country_code):
    web_url = f"http://www.findrate.tw/{country_code}/#"
    headers = {
        "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/58.0.3029.81 Safari/537.36")
    }
    resp = get_web_page(web_url, headers)
    soup = BeautifulSoup(resp.text, "lxml")

    h2_list = soup.findAll("h2")
    for h2 in h2_list:
        h2_text = encode_iso8859_to_utf8(h2.text)
        if "推薦銀行" in h2_text:
            recom_bk_text = h2_text

    th11_list = list()
    th_list = td_list = soup.findAll("th")
    for th in th_list[0:3]:
        th11_list.append(encode_iso8859_to_utf8(th.text))

    td_list = soup.findAll("td")
    recom_list1 = list()
    recom_list2 = list()
    bktd_position_dict = dict()
    for i, td in enumerate(td_list):
        td_text = encode_iso8859_to_utf8(td.text)

        if i < 3:
            recom_list1.append(td_text)

        elif i < 7 and i >= 4:
            recom_list2.append(td_text)

        if td_text == "國泰世華":
            bktd_position_dict.update({"國泰世華": i})

        if td_text == "第一銀行":
            bktd_position_dict.update({"第一銀行": i})

        if td_text == "臺灣銀行":
            bktd_position_dict.update({"臺灣銀行": i})

    # table title
    title_list = list()
    for th_i in [4, 7, 8]:
        title_text = encode_iso8859_to_utf8(th_list[th_i].text)
        title_list.append(title_text)

    # Bank contents
    bk_content_dict = dict()
    for bk_i in bktd_position_dict:
        bk_position = bktd_position_dict[bk_i]
        cub_list = list()
        for cub_i in [bk_position + 3, bk_position + 4]:
            cub_text = encode_iso8859_to_utf8(td_list[cub_i].text)
            cub_list.append(float(cub_text))
        bk_content_dict.update({bk_i: cub_list})

    summery_dict = dict()
    summery_dict["recombk_text"] = recom_bk_text
    summery_dict["recombk_title"] = th11_list
    summery_dict["recombk1"] = recom_list1
    summery_dict["recombk2"] = recom_list2
    summery_dict["bk_tb_title"] = title_list
    summery_dict["bk_content"] = bk_content_dict

    return summery_dict


def get_line_msg_format():
    """
        "bk_content": {
            "臺灣銀行": [30.815, 30.915],
            "第一銀行": [30.78, 30.96],
            "國泰世華": [30.78, 30.98]
        },
        "bk_tb_title":
            ["銀行名稱", "即期買入", "即期賣出"]
    """
    country_list = ["USD", "JPY", "CAD", "EUR"]
    msg = "臺灣銀行\n------------------\n"
    for country_i in country_list:
        summery_dict = get_foreign_currency(country_code=country_i)

        title = summery_dict["recombk_text"].split("/")[0]
        msg += "【{}】\n即期買入   即期賣出\n".format(title)

        RTBuyIn = summery_dict["bk_content"]["臺灣銀行"][0]
        RTSellOut = summery_dict["bk_content"]["臺灣銀行"][1]
        msg += "{}      {}\n".format(RTBuyIn, RTSellOut)
        msg += "------------------\n"

    print(msg)

    return msg.strip()


def get_gold_prise():
    web_url = "https://www.goldlegend.com/"
    headers = {
        'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/58.0.3029.81 Safari/537.36')
    }
    resp = get_web_page(web_url, headers)
    soup = BeautifulSoup(resp.text, "lxml")

    gold_price_buy = soup.find("span", {"class": "goldprice_tw_buy"}).text
    gold_price_sell = soup.find("span", {"class": "goldprice_tw_sell"}).text

    line_msg_format = "\n今日黃金價格 - (TWD/錢)\n買進:  {}\n賣出:  {}".format(
        gold_price_buy, gold_price_sell)
    print(line_msg_format)
    return line_msg_format


if __name__ == "__main__":
    token = os.environ["LINE_TOKEN"]
    foreign_currency_msg = get_line_msg_format()
    line_notify(token, foreign_currency_msg)

    gold_prise_msg = get_gold_prise()
    line_notify(token, gold_prise_msg)
