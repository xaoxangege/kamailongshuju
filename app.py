from flask import Flask, jsonify, render_template
import requests
from bs4 import BeautifulSoup
import re
from collections import defaultdict

app = Flask(__name__)

url = 'https://book4.kitjit2.com/day_xb.php?phpname=jizhang88_bot&chat_id=-1002406164474'

def normalize_user(user):
    clean_name_pattern = r'[^a-zA-Z\u4e00-\u9fa5]'
    if '𝐉𝐚𝐦𝐞𝐬' in user:
        user = 'James'
    elif '⚡️『🅰️🅻🅴🆇』⚡️' in user:
        user = 'Alex'
    else:
        user = re.sub(clean_name_pattern, '', user)
    replacements = {
        '大个SVIP': '大个',
        '大象八方来财': '大象',
        'David二踢脚': 'David'
    }
    for k, v in replacements.items():
        if k in user:
            user = v
    return user

def calculate_group_stats(stat_data):
    groups = [
        '小猫', '阿远', '传奇', '大猫',
        '佩恩', 'JC', '龙猫', '大象',
        '小杰', '大个', '霄贤', '唐宇',
        '宏图', '大花', '阿杰',
        '老三', '昊坤', '阿凯', '小振',
        '阿亿', '千亿', '一锅', '吉雅'
    ]
    totals = dict.fromkeys(groups, 0.0)
    for user, _, deposit in stat_data:
        try:
            deposit_val = float(deposit)
        except:
            deposit_val = 0
        if user in totals:
            totals[user] += deposit_val

    group_lines = [
        ['小猫', '阿远', '传奇', '大猫'],
        ['佩恩', 'JC', '龙猫', '大象'],
        ['小杰', '大个', '霄贤', '唐宇'],
        ['大花', '阿杰', '宏图'],
        ['昊坤', '阿凯', '小振','老三'],
        ['千亿', '一锅', '吉雅', '阿亿']
    ]

    result = []
    for line in group_lines:
        line_data = [{"name": name, "value": int(totals[name])} for name in line]
        total_value = sum(item["value"] for item in line_data)
        line_data.append({"name": "总计", "value": total_value})
        result.append(line_data)

    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/main_data')
def get_main_data():
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    stat_box = soup.find_all('div', class_='box-body')
    if len(stat_box) < 3:
        return jsonify({"data": [], "group_summary": ""})
    table = stat_box[2].find('table')
    rows = table.find_all('tr')[1:]
    pattern = r'\((\d+)笔\)'
    data = []
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 4:
            user = cols[0].text.strip()
            deposit = cols[1].text.strip()
            match = re.search(pattern, user)
            transactions = match.group(1) if match else '0'
            user = user.split('(')[0].strip()
            user = normalize_user(user)
            deposit_amount = deposit.split('/')[0].strip()
            data.append([user, transactions, deposit_amount])

    group_summary = calculate_group_stats(data)

    return jsonify({
    "data": data,
    "group_summary": group_summary
    })

@app.route('/sub_data')
def get_sub_data():
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('div', class_='box-body').find('table')
    rows = table.find_all('tr')[1:]
    bins = [2000, 5000, 10000, 15000, 20000]
    grouped = defaultdict(lambda: dict.fromkeys(bins, 0))
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 3:
            try:
                amount = int(re.sub(r'\D', '', cols[1].text))
            except:
                amount = 0
            marker = re.sub(r'[^a-zA-Z\u4e00-\u9fa5]', '', cols[2].text.strip())
            marker = normalize_user(marker)
            for b in bins[::-1]:
                if amount >= b:
                    grouped[marker][b] += 1
                    break
    data = []
    for user, bin_counts in grouped.items():
        row = [user] + [bin_counts[b] for b in bins]
        data.append(row)
    total = ["总计"] + [sum(row[i] for row in data) for i in range(1, 6)]
    data.append(total)
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

