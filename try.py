import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

# 邮箱配置
mail_host = "smtp.qq.com"
mail_port = 465
mail_user = "3668515797@qq.com"
mail_pass = "duogomblwaguchge"  # 授权码！

sender = "3668515797@qq.com"
receivers = ["turturtur250@gmail.com"]  # 目标邮箱

# 邮件内容
message = MIMEText("这是一封来自颐康云平台的测试邮件 ✉️", "plain", "utf-8")
message["From"] = formataddr(("颐康云平台", sender))  # ✅ 正确格式
message["To"] = formataddr(("用户", receivers[0]))
message["Subject"] = Header("测试邮件", "utf-8")

try:
    smtp = smtplib.SMTP_SSL(mail_host, mail_port)
    smtp.login(mail_user, mail_pass)
    smtp.sendmail(sender, receivers, message.as_string())
    smtp.quit()
    print("✅ 邮件发送成功")
except Exception as e:
    print("❌ 邮件发送失败：", e)
