import requests, json, re, os
import time

# 机场的地址
url = os.environ.get('URL')
# 配置用户名（一般是邮箱）
config = os.environ.get('CONFIG')
# server酱
SCKEY = os.environ.get('SCKEY')
# Telegram 设置
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 日志收集器
logs = []
start_time = time.time()

def log(message):
    """记录日志并添加到日志收集器"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    log_message = f'[{timestamp}] {message}'
    logs.append(log_message)
    print(log_message)

def send_to_telegram(title, message):
    """发送消息到 Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log("Telegram 环境变量未设置，跳过推送")
        return
    
    try:
        # 创建报告
        duration = int(time.time() - start_time)
        report = f"*{title}*\n\n{message}\n\n⏱️ 运行时长: {duration} 秒"
        
        # 发送消息
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': report,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, data=payload)
        
        if response.status_code == 200:
            log("Telegram 推送成功")
        else:
            log(f"Telegram 推送失败: {response.text}")
    except Exception as e:
        log(f"发送到 Telegram 时出错: {str(e)}")

def sign(order, user, pwd):
    """执行签到操作"""
    session = requests.session()
    global url, SCKEY
    
    header = {
        'origin': url,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
    }
    data = {
        'email': user,
        'passwd': pwd
    }
    
    try:
        log(f'=== 账号{order}进行登录... ===')
        log(f'账号：{user}')
        
        res = session.post(url=f'{url}/auth/login', headers=header, data=data).text
        log(f'登录响应: {res}')
        
        response = json.loads(res)
        log(response['msg'])
        
        # 进行签到
        res2 = session.post(url=f'{url}/user/checkin', headers=header).text
        log(f'签到响应: {res2}')
        
        result = json.loads(res2)
        log(result['msg'])
        
        content = result['msg']
        title = f"机场签到成功 - 账号{order}"
        
        # 推送到 Server酱
        if SCKEY:
            push_url = f'https://sctapi.ftqq.com/{SCKEY}.send?title={title}&desp={content}'
            requests.post(url=push_url)
            log('Server酱推送成功')
        
        # 添加到最终报告
        return f"✅ 账号{order} ({user}) 签到成功: {content}\n"
        
    except Exception as ex:
        content = f'签到失败: {str(ex)}'
        log(content)
        title = f"机场签到失败 - 账号{order}"
        
        # 推送到 Server酱
        if SCKEY:
            push_url = f'https://sctapi.ftqq.com/{SCKEY}.send?title={title}&desp={content}'
            requests.post(url=push_url)
            log('Server酱推送成功')
        
        # 添加到最终报告
        return f"❌ 账号{order} ({user}) 签到失败: {str(ex)}\n"

if __name__ == '__main__':
    # 初始化日志
    log("🚀 开始执行机场签到任务")
    log(f"机场地址: {url}")
    
    results = []
    
    # 处理账号配置
    if not config:
        error_msg = "❌ 错误: 未设置 CONFIG 环境变量"
        log(error_msg)
        send_to_telegram("机场签到失败", error_msg)
        exit()
    
    configs = config.splitlines()
    if len(configs) % 2 != 0 or len(configs) == 0:
        error_msg = "❌ 配置文件格式错误: 账号密码必须成对出现"
        log(error_msg)
        send_to_telegram("机场签到失败", error_msg)
        exit()
    
    user_quantity = len(configs) // 2
    log(f"找到 {user_quantity} 个账号")
    
    # 依次处理每个账号
    for i in range(user_quantity):
        user = configs[i*2]
        pwd = configs[i*2+1]
        result = sign(i, user, pwd)
        results.append(result)
    
    # 创建最终报告
    duration = int(time.time() - start_time)
    final_report = f"🏁 机场签到任务完成\n\n"
    final_report += f"⏱️ 总用时: {duration} 秒\n"
    final_report += f"👤 账号数量: {user_quantity}\n\n"
    final_report += "📋 签到结果:\n"
    final_report += "".join(results)
    
    # 发送最终报告到 Telegram
    log("\n" + final_report)
    send_to_telegram("机场签到完成", final_report)
    
    log("✅ 所有账号签到完成")
