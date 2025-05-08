import instaloader
import re
import json
from time import sleep
from getpass import getpass

class AdvancedInstagramOSINT:
    def __init__(self):
        self.loader = instaloader.Instaloader()
        self.contact_pattern = re.compile(r'(\+?\d[\d\- ]{7,}\d)|([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})')
        
    def login(self):
        """تسجيل الدخول بحساب إنستجرام"""
        try:
            username = input("Enter Instagram username: ")
            password = getpass("Enter password: ")
            self.loader.login(username, password)
            return True
        except Exception as e:
            print(f"Login failed: {e}")
            return False

    def extract_contacts(self, text):
        """استخراج أرقام الهواتف وعناوين البريد الإلكتروني من النص"""
        return self.contact_pattern.findall(text)

    def get_profile_contacts(self, username):
        """جمع معلومات الاتصال من الملف الشخصي"""
        try:
            profile = instaloader.Profile.from_username(self.loader.context, username)
            profile_data = {
                'bio': profile.biography,
                'external_url': profile.external_url
            }
            
            contacts = {}
            for field, text in profile_data.items():
                if text:
                    found = self.extract_contacts(text)
                    if found:
                        contacts[field] = [item for sublist in found for item in sublist if item]
            
            return contacts
        except Exception as e:
            return {'error': str(e)}

    def scan_posts_for_contacts(self, username, limit=10):
        """فحص المنشورات للعثور على معلومات الاتصال"""
        try:
            profile = instaloader.Profile.from_username(self.loader.context, username)
            posts = profile.get_posts()
            
            post_contacts = {}
            post_count = 0
            
            for post in posts:
                if post_count >= limit:
                    break
                    
                post_data = {
                    'caption': post.caption,
                    'comments': []
                }
                
                # جمع التعليقات
                for comment in post.get_comments():
                    post_data['comments'].append(comment.text)
                    sleep(1)  # تجنب حظر المعدل الزمني
                
                # استخراج جهات الاتصال
                contacts = {}
                if post.caption:
                    caption_contacts = self.extract_contacts(post.caption)
                    if caption_contacts:
                        contacts['caption'] = [item for sublist in caption_contacts for item in sublist if item]
                
                comment_contacts = []
                for comment in post_data['comments']:
                    found = self.extract_contacts(comment)
                    if found:
                        comment_contacts.extend([item for sublist in found for item in sublist if item])
                
                if comment_contacts:
                    contacts['comments'] = comment_contacts
                
                if contacts:
                    post_contacts[post.shortcode] = contacts
                
                post_count += 1
                sleep(2)  # تجنب حظر المعدل الزمني
            
            return post_contacts
        except Exception as e:
            return {'error': str(e)}

    def get_full_profile_report(self, username):
        """تقرير كامل عن الحساب مع معلومات الاتصال"""
        try:
            print(f"\n[+] Collecting data for {username}...")
            
            # معلومات الملف الشخصي الأساسية
            profile = instaloader.Profile.from_username(self.loader.context, username)
            profile_info = {
                'username': profile.username,
                'full_name': profile.full_name,
                'user_id': profile.userid,
                'is_private': profile.is_private,
                'followers': profile.followers,
                'following': profile.followees,
                'bio': profile.biography,
                'external_url': profile.external_url,
                'profile_pic_url': profile.profile_pic_url
            }
            
            # معلومات الاتصال من الملف الشخصي
            print("[+] Scanning profile for contact info...")
            profile_contacts = self.get_profile_contacts(username)
            
            # معلومات الاتصال من المنشورات
            print("[+] Scanning recent posts for contact info...")
            post_contacts = self.scan_posts_for_contacts(username)
            
            # تجميع كل البيانات
            full_report = {
                'profile_info': profile_info,
                'profile_contacts': profile_contacts,
                'post_contacts': post_contacts
            }
            
            return full_report
        except Exception as e:
            return {'error': str(e)}

    def save_report(self, data, filename):
        """حفظ التقرير في ملف JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"\n[+] Report saved to {filename}")

def main():
    tool = AdvancedInstagramOSINT()
    
    if not tool.login():
        return
    
    username = input("\nEnter target Instagram username: ")
    report = tool.get_full_profile_report(username)
    
    if 'error' in report:
        print(f"\n[-] Error: {report['error']}")
    else:
        filename = f"{username}_full_report.json"
        tool.save_report(report, filename)
        
        # عرض ملخص للنتائج
        print("\n[+] Contact Information Summary:")
        
        # جهات الاتصال من الملف الشخصي
        profile_contacts = report.get('profile_contacts', {})
        if profile_contacts:
            print("\nFrom Profile:")
            for field, contacts in profile_contacts.items():
                if contacts:
                    print(f"  {field.capitalize()}:")
                    for contact in contacts:
                        print(f"    - {contact}")
        else:
            print("\nNo contact info found in profile.")
        
        # جهات الاتصال من المنشورات
        post_contacts = report.get('post_contacts', {})
        if post_contacts:
            print("\nFrom Posts:")
            for post_id, contacts in post_contacts.items():
                print(f"\nPost: https://instagram.com/p/{post_id}")
                if 'caption' in contacts and contacts['caption']:
                    print("  Caption:")
                    for contact in contacts['caption']:
                        print(f"    - {contact}")
                if 'comments' in contacts and contacts['comments']:
                    print("  Comments:")
                    for contact in contacts['comments']:
                        print(f"    - {contact}")
        else:
            print("\nNo contact info found in posts.")

if __name__ == "__main__":
    main()
