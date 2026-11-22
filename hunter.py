import urllib.request
import socket
import concurrent.futures
import requests
import time
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# بياناتك الخاصة
BOT_TOKEN = "8408869152:AAG9LriUSq8PkPj5lz6dqFkQQoEPOAQ2Wtw"
CHAT_ID = "1415636083"
DOMAIN = "purple-silence-2aa6.hussin20071h.workers.dev" # نطاق سيرفرك

def get_cloudflare_ips():
    try:
        req = urllib.request.Request("https://api.cloudflare.com/client/v4/ips")
        response = urllib.request.urlopen(req)
        data = response.read().decode('utf-8')
        ips = json.loads(data)['result']['ipv4_cidrs']
        ip_list = []
        for ip_range in ips:
            base_ip = ip_range.split('/')[0]
            # توليد عناوين من كل نطاق
            for i in range(1, 20): 
                parts = base_ip.split('.')
                parts[3] = str(i)
                ip_list.append('.'.join(parts))
        return ip_list
    except Exception as e:
        print(f"Error fetching IPs: {e}")
        return []

def test_ip(ip):
    try:
        start = time.time()
        # اختبار الاتصال الفعلي عبر السيرفر
        requests.get(f"https://{ip}/", headers={"Host": DOMAIN}, timeout=2, verify=False)
        latency = (time.time() - start) * 1000
        return (ip, latency)
    except:
        return None

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error sending message: {e}")

def main():
    print("Starting hunt...")
    ips = get_cloudflare_ips()
    
    if not ips:
        send_telegram_message("❌ حدث خطأ أثناء جلب عناوين IP.")
        return

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(test_ip, ip) for ip in ips]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
    
    # ترتيب النتائج حسب أقل بينج
    results.sort(key=lambda x: x[1])
    top_5 = results[:5]
    
    if top_5:
        message = f"🏆 **أفضل 5 عناوين IP لسيرفرك:**\n\n"
        for ip, latency in top_5:
            message += f"✅ `{ip}` | البينج: {latency:.0f}ms\n"
        
        message += f"\n💡 **كيف تستخدمها؟**\nضع أحد هذه العناوين في تطبيق v2rayNG في خانة (Address) بدلاً من النطاق الطويل."
        send_telegram_message(message)
        print("Message sent successfully!")
    else:
        send_telegram_message("⚠️ لم يتم العثور على أي IP يعمل في هذه الدورة. سأحاول مرة أخرى لاحقاً.")

if __name__ == "__main__":
    main()
