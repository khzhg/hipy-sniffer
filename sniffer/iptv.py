import json
import time
from datetime import datetime
import concurrent.futures
from asyncSnifferPro import Sniffer
from iptv_urls import *
from pathlib import Path
import asyncio
import requests
import re
import os
import threading
from queue import Queue
import eventlet

eventlet.monkey_patch()
today = datetime.now()
formatted_date = today.strftime('%Y年%m月%d日')[2:]

config_path = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '../quart_config.json'))).as_posix()
print(config_path)
if not os.path.exists(config_path):
    exit(f"config_path not found for {config_path}")

with open(config_path, encoding='utf-8') as f:
    config_dict = json.loads(f.read())
print(config_dict)
save_path = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '../static/lives'))).as_posix()
if not os.path.exists(save_path):
    os.makedirs(save_path, exist_ok=True)
print('save_path:', save_path)
t1 = time.time()
urls = urls2

replace_dict1 = {
    "cctv": "CCTV",
    "中央": "CCTV",
    "央视": "CCTV",
    "高清": "",
    "超高": "",
    "HD": "",
    "标清": "",
    "频道": "",
    "-": "",
    " ": "",
    "PLUS": "+",
    "＋": "+",
    "(": "",
    ")": "",
}

replace_dict2 = {
    "CCTV1综合": "CCTV1",
    "CCTV2财经": "CCTV2",
    "CCTV3综艺": "CCTV3",
    "CCTV4国际": "CCTV4",
    "CCTV4中文国际": "CCTV4",
    "CCTV4欧洲": "CCTV4",
    "CCTV5体育": "CCTV5",
    "CCTV6电影": "CCTV6",
    "CCTV7军事": "CCTV7",
    "CCTV7军农": "CCTV7",
    "CCTV7农业": "CCTV7",
    "CCTV7国防军事": "CCTV7",
    "CCTV8电视剧": "CCTV8",
    "CCTV9记录": "CCTV9",
    "CCTV9纪录": "CCTV9",
    "CCTV10科教": "CCTV10",
    "CCTV11戏曲": "CCTV11",
    "CCTV12社会与法": "CCTV12",
    "CCTV13新闻": "CCTV13",
    "CCTV新闻": "CCTV13",
    "CCTV14少儿": "CCTV14",
    "CCTV15音乐": "CCTV15",
    "CCTV16奥林匹克": "CCTV16",
    "CCTV17农业农村": "CCTV17",
    "CCTV17农业": "CCTV17",
    "CCTV5+体育赛视": "CCTV5+",
    "CCTV5+体育赛事": "CCTV5+",
    "CCTV5+体育": "CCTV5+",
}


def modify_urls(url):
    modified_urls = []
    ip_start_index = url.find("//") + 2
    ip_end_index = url.find(":", ip_start_index)
    base_url = url[:ip_start_index]  # http:// or https://
    ip_address = url[ip_start_index:ip_end_index]
    port = url[ip_end_index:]
    ip_end = "/iptv/live/1000.json?key=txiptv"
    for i in range(1, 256):
        modified_ip = f"{ip_address[:-1]}{i}"
        modified_url = f"{base_url}{modified_ip}{port}{ip_end}"
        modified_urls.append(modified_url)

    return modified_urls


def is_url_accessible(url):
    try:
        response = requests.get(url, timeout=0.5)
        if response.status_code == 200:
            return url
    except requests.exceptions.RequestException:
        pass
    return None


results = []


async def get_page_content(url):
    # async with Sniffer(debug=True, headless=True) as browser:
    async with Sniffer(debug=config_dict['DEBUG'], headless=config_dict['SNIFFER_HEADLESS'],
                       use_chrome=config_dict['USE_CHROME'], init_new_page=False) as browser:
        # 在这里，async_func已被调用并已完成
        pass
    page = await browser.browser.new_page()
    await page.expose_function("log", lambda *args: print(*args))
    js = """
Object.defineProperties(navigator, {webdriver: {get: () => undefined}});
Object.defineProperties(navigator, {platform: {get: () => 'iPhone'}});
    """
    await page.add_init_script(js)
    await page.goto(url)  #
    try:
        await page.wait_for_timeout(10000)
        content = await page.content()
    except Exception as e:
        print(f'get_page_content错误: {e}')
        content = ''
    await browser.close()
    return content


urls_count = len(urls)
for index, url in enumerate(urls):
    print(f'get_page_content for {url} ({index + 1}/{urls_count})')
    page_content = asyncio.run(get_page_content(url))
    # print(len(page_content))
    # 查找所有符合指定格式的网址
    pattern = r"http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+"  # 设置匹配的格式，如http://8.8.8.8:8888
    urls_all = re.findall(pattern, page_content)
    # urls = list(set(urls_all))  # 去重得到唯一的URL列表
    urls = set(urls_all)  # 去重得到唯一的URL列表
    x_urls = []
    for url in urls:  # 对urls进行处理，ip第四位修改为1，并去重
        url = url.strip()
        ip_start_index = url.find("//") + 2
        ip_end_index = url.find(":", ip_start_index)
        ip_dot_start = url.find(".") + 1
        ip_dot_second = url.find(".", ip_dot_start) + 1
        ip_dot_three = url.find(".", ip_dot_second) + 1
        base_url = url[:ip_start_index]  # http:// or https://
        ip_address = url[ip_start_index:ip_dot_three]
        port = url[ip_end_index:]
        ip_end = "1"
        modified_ip = f"{ip_address}{ip_end}"
        x_url = f"{base_url}{modified_ip}{port}"
        x_urls.append(x_url)
    urls = set(x_urls)  # 去重得到唯一的URL列表
    print(len(urls), urls)
    if len(urls) < 1:
        continue
    # max_workers = min(max(len(urls), 1), 100)
    max_workers = 100
    # print(f'max_workers:{max_workers}')
    valid_urls = []
    #   多线程获取可用url
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for url in urls:
            url = url.strip()
            modified_urls = modify_urls(url)
            # print(f'modified_urls:{modified_urls}')
            for modified_url in modified_urls:
                futures.append(executor.submit(is_url_accessible, modified_url))

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                valid_urls.append(result)

    for url in valid_urls:
        print(url)
    # 遍历网址列表，获取JSON文件并解析
    for url in valid_urls:
        try:
            # 发送GET请求获取JSON文件，设置超时时间为0.5秒
            ip_start_index = url.find("//") + 2
            ip_dot_start = url.find(".") + 1
            ip_index_second = url.find("/", ip_dot_start)
            base_url = url[:ip_start_index]  # http:// or https://
            ip_address = url[ip_start_index:ip_index_second]
            url_x = f"{base_url}{ip_address}"

            json_url = f"{url}"
            response = requests.get(json_url, timeout=0.5)
            json_data = response.json()

            try:
                # 解析JSON文件，获取name和url字段
                for item in json_data['data']:
                    if isinstance(item, dict):
                        name = item.get('name')
                        urlx = item.get('url')
                        if ',' in urlx:
                            urlx = f"aaaaaaaa"
                        # if 'http' in urlx or 'udp' in urlx or 'rtp' in urlx:
                        if 'http' in urlx:
                            urld = f"{urlx}"
                        else:
                            urld = f"{url_x}{urlx}"

                        if name and urlx:
                            # 删除特定文字
                            for key, value in replace_dict1.items():
                                name = name.replace(key, value)
                            name = re.sub(r"CCTV(\d+)台", r"CCTV\1", name)
                            for key, value in replace_dict2.items():
                                name = name.replace(key, value)
                            results.append(f"{name},{urld}")
            except:
                continue
        except:
            continue

channels = []

for result in results:
    line = result.strip()
    if result:
        channel_name, channel_url = result.split(',')
        channels.append((channel_name, channel_url))

# 线程安全的队列，用于存储下载任务
task_queue = Queue()

# 线程安全的列表，用于存储结果
results = []

error_channels = []


# 定义工作线程函数
def worker():
    while True:
        # 从队列中获取一个任务
        channel_name, channel_url = task_queue.get()
        try:
            channel_url_t = channel_url.rstrip(channel_url.split('/')[-1])  # m3u8链接前缀
            lines = requests.get(channel_url, timeout=1).text.strip().split('\n')  # 获取m3u8文件内容
            ts_lists = [line.split('/')[-1] for line in lines if line.startswith('#') == False]  # 获取m3u8文件下视频流后缀
            ts_lists_0 = ts_lists[0].rstrip(ts_lists[0].split('.ts')[-1])  # m3u8链接前缀
            ts_url = channel_url_t + ts_lists[0]  # 拼接单个视频片段下载链接

            # 多获取的视频数据进行5秒钟限制
            with eventlet.Timeout(5, False):
                start_time = time.time()
                content = requests.get(ts_url, timeout=1).content
                end_time = time.time()
                response_time = (end_time - start_time) * 1

            if content:
                with open(ts_lists_0, 'ab') as f:
                    f.write(content)  # 写入文件
                file_size = len(content)
                # print(f"文件大小：{file_size} 字节")
                download_speed = file_size / response_time / 1024
                # print(f"下载速度：{download_speed:.3f} kB/s")
                normalized_speed = min(max(download_speed / 1024, 0.001), 100)  # 将速率从kB/s转换为MB/s并限制在1~100之间
                # print(f"标准化后的速率：{normalized_speed:.3f} MB/s")

                # 删除下载的文件
                os.remove(ts_lists_0)
                result = channel_name, channel_url, f"{normalized_speed:.3f} MB/s"
                results.append(result)
                numberx = (len(results) + len(error_channels)) / len(channels) * 100
                print(
                    f"可用频道：{len(results)} 个 , 不可用频道：{len(error_channels)} 个 , 总频道：{len(channels)} 个 ,总进度：{numberx:.2f} %。")
        except:
            error_channel = channel_name, channel_url
            error_channels.append(error_channel)
            numberx = (len(results) + len(error_channels)) / len(channels) * 100
            print(
                f"可用频道：{len(results)} 个 , 不可用频道：{len(error_channels)} 个 , 总频道：{len(channels)} 个 ,总进度：{numberx:.2f} %。")

        # 标记任务完成
        task_queue.task_done()


# 创建多个工作线程
num_threads = 10
for _ in range(num_threads):
    t = threading.Thread(target=worker, daemon=True)  # 将工作线程设置为守护线程
    t.start()

# 添加下载任务到队列
for channel in channels:
    task_queue.put(channel)

# 等待所有任务完成
task_queue.join()


def channel_key(channel_name):
    match = re.search(r'\d+', channel_name)
    if match:
        return int(match.group())
    else:
        return float('inf')  # 返回一个无穷大的数字作为关键字


# 对频道进行排序
results.sort(key=lambda x: (x[0], -float(x[2].split()[0])))
results.sort(key=lambda x: channel_key(x[0]))

result_counter = 8  # 每个频道需要的个数
first_channel_url = results[0][1]
with open(os.path.join(save_path, "lives.txt"), 'w', encoding='utf-8') as file:
    channel_counters = {}
    file.write('🌏｜央视频道,#genre#\n')
    for result in results:
        channel_name, channel_url, speed = result
        if 'CCTV' in channel_name:
            if channel_name in channel_counters:
                if channel_counters[channel_name] >= result_counter:
                    continue
                else:
                    file.write(f"{channel_name},{channel_url}\n")
                    channel_counters[channel_name] += 1
            else:
                file.write(f"{channel_name},{channel_url}\n")
                channel_counters[channel_name] = 1
    channel_counters = {}
    file.write('🛰｜卫视频道,#genre#\n')
    for result in results:
        channel_name, channel_url, speed = result
        if '卫视' in channel_name:
            if channel_name in channel_counters:
                if channel_counters[channel_name] >= result_counter:
                    continue
                else:
                    file.write(f"{channel_name},{channel_url}\n")
                    channel_counters[channel_name] += 1
            else:
                file.write(f"{channel_name},{channel_url}\n")
                channel_counters[channel_name] = 1
    channel_counters = {}
    file.write('👑｜其他频道,#genre#\n')
    for result in results:
        channel_name, channel_url, speed = result
        if 'CCTV' not in channel_name and '卫视' not in channel_name and '测试' not in channel_name:
            if channel_name in channel_counters:
                if channel_counters[channel_name] >= result_counter:
                    continue
                else:
                    file.write(f"{channel_name},{channel_url}\n")
                    channel_counters[channel_name] += 1
            else:
                file.write(f"{channel_name},{channel_url}\n")
                channel_counters[channel_name] = 1

    file.write(f'📺｜定期维护,#genre#\n{formatted_date}更新,{first_channel_url}\n')

with open(os.path.join(save_path, "lives.m3u"), 'w', encoding='utf-8') as file:
    channel_counters = {}
    file.write('#EXTM3U\n')
    file.write(f"{first_channel_url}\n")
    for result in results:
        channel_name, channel_url, speed = result
        if 'CCTV' in channel_name:
            if channel_name in channel_counters:
                if channel_counters[channel_name] >= result_counter:
                    continue
                else:
                    file.write(f"#EXTINF:-1 group-title=\"🌏｜央视频道\",{channel_name}\n")
                    file.write(f"{channel_url}\n")
                    channel_counters[channel_name] += 1
            else:
                file.write(f"#EXTINF:-1 group-title=\"🌏｜央视频道\",{channel_name}\n")
                file.write(f"{channel_url}\n")
                channel_counters[channel_name] = 1
    channel_counters = {}
    # file.write('卫视频道,#genre#\n')
    for result in results:
        channel_name, channel_url, speed = result
        if '卫视' in channel_name:
            if channel_name in channel_counters:
                if channel_counters[channel_name] >= result_counter:
                    continue
                else:
                    file.write(f"#EXTINF:-1 group-title=\"🛰｜卫视频道\",{channel_name}\n")
                    file.write(f"{channel_url}\n")
                    channel_counters[channel_name] += 1
            else:
                file.write(f"#EXTINF:-1 group-title=\"🛰｜卫视频道\",{channel_name}\n")
                file.write(f"{channel_url}\n")
                channel_counters[channel_name] = 1
    channel_counters = {}
    # file.write('其他频道,#genre#\n')
    for result in results:
        channel_name, channel_url, speed = result
        if 'CCTV' not in channel_name and '卫视' not in channel_name and '测试' not in channel_name:
            if channel_name in channel_counters:
                if channel_counters[channel_name] >= result_counter:
                    continue
                else:
                    file.write(f"#EXTINF:-1 group-title=\"👑｜其他频道\",{channel_name}\n")
                    file.write(f"{channel_url}\n")
                    channel_counters[channel_name] += 1
            else:
                file.write(f"#EXTINF:-1 group-title=\"👑｜其他频道\",{channel_name}\n")
                file.write(f"{channel_url}\n")
                channel_counters[channel_name] = 1

    file.write(f"#EXTINF:-1 group-title=\"📺｜定期维护\",{formatted_date}更新\n")
    file.write(f"{first_channel_url}\n")

t2 = time.time()
print(f'共计耗时:{round(t2 - t1, 2)}秒')
