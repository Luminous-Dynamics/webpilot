#!/usr/bin/env python3
"""
Email Automation for Real Productivity
Actually checks and manages emails through web interfaces.
"""

import time
from typing import List, Dict, Optional
from src.webpilot.core import RealBrowserAutomation  # Now uses Playwright!


class EmailAutomation:
    """
    Automate email through web interfaces (Gmail, Outlook Web, etc.)
    Real automation that actually works with your email.
    """
    
    def __init__(self, email_provider='gmail'):
        self.provider = email_provider
        self.browser = RealBrowserAutomation(headless=False)  # Visible for email
        self.logged_in = False
        
        # Provider URLs
        self.urls = {
            'gmail': 'https://mail.google.com',
            'outlook': 'https://outlook.live.com',
            'yahoo': 'https://mail.yahoo.com'
        }
    
    def login(self, email: str, password: str = None) -> bool:
        """
        Login to email provider.
        For security, can use environment variables or prompts for password.
        """
        if not self.browser.start():
            print("❌ Failed to start browser")
            return False
        
        # Navigate to email provider
        url = self.urls.get(self.provider, self.urls['gmail'])
        self.browser.navigate(url)
        time.sleep(2)
        
        # Gmail login flow
        if self.provider == 'gmail':
            # Enter email
            self.browser.type_text(email, "Email or phone")
            self.browser.click("Next")
            time.sleep(2)
            
            if password:
                # Enter password (only if provided)
                self.browser.type_text(password, "Enter your password")
                self.browser.click("Next")
                time.sleep(3)
            else:
                print("⚠️  Manual password entry required for security")
                input("Press Enter after logging in manually...")
            
            # Check if logged in
            if "inbox" in self.browser.get_current_url().lower():
                self.logged_in = True
                print("✅ Logged into Gmail")
                return True
        
        return False
    
    def check_inbox(self, limit: int = 10) -> List[Dict]:
        """Check inbox and return list of emails."""
        if not self.logged_in:
            print("❌ Not logged in")
            return []
        
        emails = []
        
        # Gmail inbox parsing
        if self.provider == 'gmail':
            # Click inbox if not there
            if "inbox" not in self.browser.get_current_url():
                self.browser.click("Inbox")
                time.sleep(2)
            
            # Get page content
            page_text = self.browser.get_text()
            
            # Simple parsing (would need refinement for production)
            lines = page_text.split('\n')
            current_email = {}
            
            for line in lines[:limit * 5]:  # Rough estimate
                if '@' in line and '.' in line:  # Likely sender
                    if current_email:
                        emails.append(current_email)
                    current_email = {'sender': line}
                elif current_email and 'subject' not in current_email:
                    # Next non-empty line after sender is usually subject
                    if line.strip():
                        current_email['subject'] = line
                        current_email['unread'] = 'unread' in page_text.lower()
            
            if current_email:
                emails.append(current_email)
        
        return emails[:limit]
    
    def search_emails(self, query: str) -> bool:
        """Search for emails."""
        if not self.logged_in:
            return False
        
        # Find search box and search
        if self.provider == 'gmail':
            self.browser.type_text(query, "Search mail")
            self.browser.execute_script(
                "document.querySelector('[aria-label=\"Search mail\"]').form.submit()"
            )
            time.sleep(2)
            print(f"✅ Searched for: {query}")
            return True
        
        return False
    
    def compose_email(self, to: str, subject: str, body: str) -> bool:
        """Compose a new email."""
        if not self.logged_in:
            return False
        
        if self.provider == 'gmail':
            # Click compose
            self.browser.click("Compose")
            time.sleep(2)
            
            # Fill in recipient
            self.browser.type_text(to, "Recipients")
            time.sleep(1)
            
            # Fill in subject
            self.browser.type_text(subject, "Subject")
            time.sleep(1)
            
            # Fill in body
            self.browser.type_text(body, "Message Body")
            
            print(f"✅ Email composed to: {to}")
            return True
        
        return False
    
    def send_email(self) -> bool:
        """Send the composed email."""
        if not self.logged_in:
            return False
        
        if self.provider == 'gmail':
            # Look for send button
            if self.browser.click("Send"):
                print("✅ Email sent!")
                return True
        
        return False
    
    def reply_to_email(self, reply_text: str) -> bool:
        """Reply to currently open email."""
        if not self.logged_in:
            return False
        
        if self.provider == 'gmail':
            # Click reply
            self.browser.click("Reply")
            time.sleep(2)
            
            # Type reply
            self.browser.type_text(reply_text, "Message Body")
            
            # Send
            self.browser.click("Send")
            print("✅ Reply sent")
            return True
        
        return False
    
    def mark_as_read(self) -> bool:
        """Mark current email as read."""
        if not self.logged_in:
            return False
        
        if self.provider == 'gmail':
            self.browser.click("Mark as read")
            return True
        
        return False
    
    def archive_email(self) -> bool:
        """Archive current email."""
        if not self.logged_in:
            return False
        
        if self.provider == 'gmail':
            self.browser.click("Archive")
            print("✅ Email archived")
            return True
        
        return False
    
    def delete_email(self) -> bool:
        """Delete current email."""
        if not self.logged_in:
            return False
        
        if self.provider == 'gmail':
            self.browser.click("Delete")
            print("✅ Email deleted")
            return True
        
        return False
    
    def logout(self):
        """Logout and close browser."""
        if self.logged_in:
            # Click profile icon and sign out
            if self.provider == 'gmail':
                # This would need refinement for production
                self.browser.execute_script(
                    "document.querySelector('[aria-label*=\"Google Account\"]').click()"
                )
                time.sleep(1)
                self.browser.click("Sign out")
            
            self.logged_in = False
        
        self.browser.close()
        print("✅ Logged out and browser closed")
    
    def quick_inbox_summary(self) -> Dict:
        """Get a quick summary of inbox status."""
        if not self.logged_in:
            return {}
        
        summary = {
            'provider': self.provider,
            'total_emails': 0,
            'unread': 0,
            'recent_senders': []
        }
        
        emails = self.check_inbox(20)
        summary['total_emails'] = len(emails)
        summary['unread'] = sum(1 for e in emails if e.get('unread'))
        summary['recent_senders'] = [e.get('sender', 'Unknown') for e in emails[:5]]
        
        return summary


def demo_email_automation():
    """Demonstrate email automation capabilities."""
    
    print("=" * 60)
    print("   Email Automation Demo")
    print("=" * 60)
    print("\n⚠️  This demo shows the structure but requires:")
    print("   - Valid email credentials")
    print("   - Manual security approval for first-time login")
    print("   - Provider-specific adjustments\n")
    
    # Example usage (would need real credentials)
    """
    email_bot = EmailAutomation('gmail')
    
    # Login (password can be from env var or secure prompt)
    email_bot.login('your.email@gmail.com')
    
    # Check inbox
    emails = email_bot.check_inbox(5)
    for email in emails:
        print(f"From: {email.get('sender')}")
        print(f"Subject: {email.get('subject')}")
        print(f"Unread: {email.get('unread')}")
        print("-" * 40)
    
    # Search for specific emails
    email_bot.search_emails("invoice")
    
    # Compose and send
    email_bot.compose_email(
        to="recipient@example.com",
        subject="Test Automation",
        body="This email was sent via browser automation!"
    )
    # email_bot.send_email()  # Uncomment to actually send
    
    # Get inbox summary
    summary = email_bot.quick_inbox_summary()
    print(f"Total emails: {summary['total_emails']}")
    print(f"Unread: {summary['unread']}")
    
    # Cleanup
    email_bot.logout()
    """
    
    print("Email automation structure ready!")
    print("\nKey features:")
    print("✓ Login to web email")
    print("✓ Check and read emails")
    print("✓ Search inbox")
    print("✓ Compose and send emails")
    print("✓ Reply to emails")
    print("✓ Archive/delete emails")
    print("✓ Inbox summary stats")


if __name__ == "__main__":
    demo_email_automation()